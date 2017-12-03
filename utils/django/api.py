# Copied and borrowed from Django REST Framework.
"""
Handled exceptions raised by API requests.

In addition Django's built in 403 and 404 exceptions are handled.
(`django.http.Http404` and `django.core.exceptions.PermissionDenied`)
"""
from __future__ import unicode_literals

import functools
import json
import logging
import math
import traceback
import six

from django.conf import settings
from django.core.exceptions import PermissionDenied as dj_PermissionDenied
from django.http.request import QueryDict
from django.http.response import HttpResponseBase, JsonResponse, Http404

from .. import exceptions as api_exc
from ..decorators import mock

_logger = logging.getLogger(__name__)


def _handle_exception(exc, context=None):
    if isinstance(exc, api_exc.APIException):
        headers = {}
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['Retry-After'] = '%d' % math.ceil(exc.wait)

        if isinstance(exc.detail, api_exc.ErrorDetail):
            data = {'code': exc.detail.code, 'message': exc.detail}
        else:
            data = {
                'code': 'error_with_detail',
                'message': 'Error with detail.',
                'detail': exc.detail
            }
        response = JsonResponse(data, status=exc.status_code)
        if headers:
            for k, v in headers.items():
                response[k] = v
        return response
    elif isinstance(exc, Http404):
        return JsonResponse({
            'code': api_exc.NotFound.default_code,
            'message': api_exc.NotFound.default_detail
        }, status=api_exc.NotFound.status_code)
    elif isinstance(exc, dj_PermissionDenied):
        return JsonResponse({
            'code': api_exc.PermissionDenied.default_code,
            'message': api_exc.PermissionDenied.default_detail
        }, status=api_exc.PermissionDenied.status_code)

    else:
        # unexpected exception, log the traceback
        _logger.warning(exc, exc_info=True)
        if settings.DEBUG:
            return JsonResponse({
                'code': 'error_with_traceback',
                'message': 'Error with traceback.',
                'traceback': traceback.format_exc()
            }, status=api_exc.APIException.status_code)
        else:
            return JsonResponse({
                'code': api_exc.APIException.default_code,
                'message': api_exc.APIException.default_detail
            }, status=api_exc.APIException.status_code)


def _parse_request_body(request):
    """
    Parse data and cache as JSON or QUERY_DICT attribute for request for
    convenience and better performance.
    """
    if not request.body:
        return

    if 'application/json' in request.META['CONTENT_TYPE']:
        try:
            if isinstance(request.body, six.string_types):
                data = json.loads(request.body)
            else:
                data = json.loads(request.body.decode('utf-8'))
        except Exception as exc:
            six.raise_from(api_exc.ParseError('Invalid JSON body.'), exc)
        # cache json data to request for better performance
        request.JSON = data
    elif (request.META['CONTENT_TYPE'] ==
            'application/x-www-form-urlencoded'):
        if request.method == 'POST':
            query_dict = request.POST
        else:
            query_dict = QueryDict(request.body)
        # cache query dict to request for better performance
        request.QUERY_DICT = query_dict
    else:
        pass


def api_view(view_func=None,
             methods=('GET', 'POST'), parse_body=False,
             login_required=False, staff_member_required=False,
             **response_kwargs):

    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                if login_required or staff_member_required:
                    if not request.user.is_authenticated():
                        raise api_exc.NotAuthenticated()
                if staff_member_required:
                    if not request.user.is_staff:
                        raise api_exc.PermissionDenied()

                if request.method not in methods:
                    raise api_exc.MethodNotAllowed(request.method)

                # parse and cache QUERY_DICT or JSON data for request
                if parse_body:
                    _parse_request_body(request)

                try:
                    result = func(request, *args, **kwargs)
                except mock.Missing as err:
                    six.reraise(api_exc.MockKeyMissing,
                                api_exc.MockKeyMissing(err.key), None)

                if result and isinstance(result, HttpResponseBase):
                    return result

                response = {'code': 'ok', 'data': result}
                return JsonResponse(response, **response_kwargs)
            except Exception as exc:
                return _handle_exception(exc)

        return wrapper

    if view_func:
        return decorator(view_func)

    return decorator


def api_token_required(validator,
                       header='HTTP_AUTHORIZATION',
                       token_field='token',
                       methods=('GET', 'POST'),
                       exclude_methods=('HEAD', 'OPTION'),
                       **response_kwargs):
    """
    Require API token provided, either through header or request parameters.
    """

    def decorator(view_func):
        @api_view(methods=methods, parse_body=True, **response_kwargs)
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if exclude_methods and request.method in exclude_methods:
                return view_func(request, *args, **kwargs)

            token = None
            # header take precedence over parameters
            if header and header in request.META:
                token = request.META[header]
            elif request.method == 'GET':
                token = request.GET.get(token_field)
            else:
                if hasattr(request, 'QUERY_DICT'):
                    token = request.QUERY_DICT.get('token')
                elif hasattr(request, 'JSON'):
                    token = request.JSON.get('token')

            if not token:
                raise api_exc.NotAuthenticated()
            if not validator(request, token):
                raise api_exc.AuthenticationFailed()

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator

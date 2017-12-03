# -*- coding:utf-8 -*-
from __future__ import absolute_import, unicode_literals

import datetime
import decimal
import json
import logging
import math
import traceback
import uuid
import six

from tornado.web import RequestHandler, HTTPError, MissingArgumentError

from .. import exceptions as api_exc
from ..decorators import mock

_logger = logging.getLogger(__name__)


class ApiJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time, decimal
    types and UUIDs.
    """
    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith('+00:00'):
                r = r[:-6] + 'Z'
            return r
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.time):
            if o.utcoffset() is not None:  # timezone aware
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r
        elif isinstance(o, datetime.timedelta):
            return self.duration_iso_string(o)
        elif isinstance(o, decimal.Decimal):
            return str(o)
        elif isinstance(o, uuid.UUID):
            return str(o)
        else:
            return super(ApiJSONEncoder, self).default(o)

    @classmethod
    def duration_iso_string(cls, duration):
        if duration < datetime.timedelta(0):
            sign = '-'
            duration *= -1
        else:
            sign = ''

        days, hours, minutes, seconds, microseconds = \
            cls._get_duration_components(duration)
        ms = '.{:06d}'.format(microseconds) if microseconds else ''
        return '{}P{}DT{:02d}H{:02d}M{:02d}{}S'.format(
            sign, days, hours, minutes, seconds, ms)

    @staticmethod
    def _get_duration_components(duration):
        days = duration.days
        seconds = duration.seconds
        microseconds = duration.microseconds

        minutes = seconds // 60
        seconds = seconds % 60

        hours = minutes // 60
        minutes = minutes % 60

        return days, hours, minutes, seconds, microseconds


class ApiRequestHandler(RequestHandler):

    def finish_json(self, data):
        chunk = json.dumps(data, cls=ApiJSONEncoder).replace("</", "<\\/")
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.finish(chunk)

    def write_error(self, status_code, **kwargs):
        exc_info = kwargs.get('exc_info')
        if not exc_info:
            self.set_status(status_code)
            self.finish_json({
                'code': 'http_%s' % status_code,
                'message': self._reason or 'Error without exception.'
            })
            return

        exc = exc_info[1]
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
            if headers:
                for k, v in headers.items():
                    self.set_header(k, v)
            self.set_status(exc.status_code)
            self.finish_json(data)
        elif isinstance(exc, mock.Missing):
            self.set_status(api_exc.MockKeyMissing.status_code)
            self.finish_json({
                'code': api_exc.MockKeyMissing.default_code,
                'message': api_exc.MockKeyMissing.default_detail.format(exc.key)
            })
        elif isinstance(exc, MissingArgumentError):
            self.set_status(exc.status_code)
            self.finish_json({
                'code': api_exc.ValidationError.default_code,
                'message': exc.log_message
            })
        elif isinstance(exc, HTTPError):
            self.set_status(exc.status_code)
            self.finish_json({
                'code': 'http_error',
                'message': str(exc)
            })
        elif status_code == 404:
            self.finish_json({
                'code': api_exc.NotFound.default_code,
                'message': api_exc.NotFound.default_detail
            })

        else:
            # unexpected exception, log the traceback
            _logger.warning(exc, exc_info=True)
            if self.settings.get('debug'):
                self.set_status(api_exc.APIException.status_code)
                self.finish_json({
                    'code': 'error_with_traceback',
                    'message': 'Error with traceback.',
                    'traceback': ''.join(traceback.format_exception(*exc_info))
                })
            else:
                self.set_status(api_exc.APIException.status_code)
                self.finish_json({
                    'code': api_exc.APIException.default_code,
                    'message': api_exc.APIException.default_detail
                })

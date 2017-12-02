# -*- coding:utf-8 -*-
from django.contrib.auth import (
    authenticate, login as auth_login, logout as auth_logout
)
from django.views.decorators.csrf import ensure_csrf_cookie

import utils.django.api as api_util
import utils.exceptions as api_exc


@ensure_csrf_cookie
@api_util.api_view(methods=('GET',))
def login_check(request):
    if not request.user.is_anonymous:
        return {'username': request.user.username}
    raise api_exc.NotAuthenticated()


@api_util.api_view(methods=('POST',), parse_body=True)
def login_ajax(request):
    data = getattr(request, 'QUERY_DICT', None)
    if not data:
        data = getattr(request, 'JSON', {})

    username = data.get('username')
    password = data.get('password')
    if not all((username, password)):
        raise api_exc.ValidationError(
            'Invalid username or password parameters.')

    user = authenticate(request, username=username, password=password)
    if not user:
        raise api_exc.AuthenticationFailed()

    auth_login(request, user)
    return {'username': user.username}


@api_util.api_view(methods=('GET',))
def logout_ajax(request):
    auth_logout(request)
    return {}

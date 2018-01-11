# -*- coding:utf-8 -*-
from django.contrib.auth import (
    authenticate, login as auth_login, logout as auth_logout
)
from django.views.decorators.csrf import ensure_csrf_cookie

import utils.django.api as api_util
import utils.exceptions as api_exc

"""
@apiDefine login User login required
The user should be already login to access this resource.
"""


@ensure_csrf_cookie
@api_util.api_view(methods=('GET',), login_required=True)
def profile(request):
    """
    @api {GET} /v1/common/users/profile 查询用戶信息
    @apiPermission login
    @apiVersion 1.0.0
    @apiName UserProfile
    @apiGroup V1-Users

    @apiSuccess {String} code 请求状态
    @apiSuccess {String} [message] 错误消息
    @apiSuccess {Object} [data] 返回数据

    @apiSuccess {String} data.username 用户名
    @apiSuccess {String} data.avatar 头像地址

    @apiSuccessExample {json} Success-Response:
        HTTP/1.1 200 OK
        {
            "code": "ok",
            "data": {
                "username": "admin",
                "avatar": "https://ss1.bdstatic.com/70cFvXSh_Q1YnxGkpoWK1HF6hhy/it/u=3448484253,3685836170&fm=27&gp=0.jpg"
            }
        }

    """  # noqa
    return {
        'username': request.user.username,
        'avatar': 'https://ss1.bdstatic.com/70cFvXSh_Q1YnxGkpoWK1HF6hhy/it/u=3448484253,3685836170&fm=27&gp=0.jpg'  # noqa
    }


@api_util.api_view(methods=('POST',), parse_body=True)
def login_ajax(request):
    """
    @api {POST} /v1/common/users/login 用戶登陆
    @apiVersion 1.0.0
    @apiName UserLogin
    @apiGroup V1-Users

    @apiParam {String} username 用戶名
    @apiParam {String} password 密碼

    @apiSuccess {String} code 请求状态
    @apiSuccess {String} [message] 错误消息
    @apiSuccess {Object} [data] 返回数据

    @apiSuccess {String} data.username 用戶名
    @apiSuccess {String} data.avatar 头像地址

    @apiSuccessExample {json} Success-Response:
        HTTP/1.1 200 OK
        {
            "code": "ok",
            "data": {
                "username": "admin",
                "avatar": "https://ss1.bdstatic.com/70cFvXSh_Q1YnxGkpoWK1HF6hhy/it/u=3448484253,3685836170&fm=27&gp=0.jpg"
            }
        }

    @apiErrorExample {json} Error-Invalid-Response:
        HTTP/1.1 400 Invalid
        {
            "code": "invalid",
            "message": "Invalid username or password parameters."
        }

    @apiErrorExample {json} Error-Failed-Response:
        HTTP/1.1 401 Unauthorized
        {
            "code": "authentication_failed",
            "message": "Incorrect authentication credentials."
        }

    """  # noqa
    data = getattr(request, '_JSON', request.POST)
    username = data.get('username')
    password = data.get('password')
    if not all((username, password)):
        raise api_exc.ValidationError(
            'Invalid username or password parameters.')

    user = authenticate(request, username=username, password=password)
    if not user:
        raise api_exc.AuthenticationFailed()

    auth_login(request, user)
    return {
        'username': user.username,
        'avatar': 'https://ss1.bdstatic.com/70cFvXSh_Q1YnxGkpoWK1HF6hhy/it/u=3448484253,3685836170&fm=27&gp=0.jpg'  # noqa
    }


@api_util.api_view(methods=('GET',))
def logout_ajax(request):
    """
    @api {GET} /v1/common/users/logout 退出登陆
    @apiVersion 1.0.0
    @apiName UserLogout
    @apiGroup V1-Users

    @apiSuccess {String} code 请求状态
    @apiSuccess {String} [message] 错误消息
    @apiSuccess {Object} [data] 返回数据

    """
    auth_logout(request)
    return {}

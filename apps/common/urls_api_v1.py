# -*- coding:utf-8 -*-

from django.conf.urls import url

from . import views_api_v1 as api_v1


urlpatterns = [
    url(r'^users/profile$', api_v1.profile),
    url(r'^users/login$', api_v1.login_ajax),
    url(r'^users/logout$', api_v1.logout_ajax),
]

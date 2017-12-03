# -*- coding:utf-8 -*-

from django.conf.urls import url

from . import views_api_v1 as api_v1


urlpatterns = [
    url(r'^profile$', api_v1.profile),
    url(r'^login$', api_v1.login_ajax),
    url(r'^logout$', api_v1.logout_ajax),
]

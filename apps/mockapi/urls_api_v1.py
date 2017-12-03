# -*- coding:utf-8 -*-

from django.conf.urls import url

from . import views_api_v1 as api_v1


urlpatterns = [
    url(r'^mock1', api_v1.mock1),
    url(r'^mock2', api_v1.Mock2View.as_view()),
]

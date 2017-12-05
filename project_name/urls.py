"""{{ project_name }} URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/{{ docs_version }}/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
import os.path
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.views import generic, static

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # vue helloworld demo
    url(r'^$', generic.TemplateView.as_view(template_name='index.html')),

    # demo user authorization and mock data APIs
    url(r'^api/v1/common/', include('apps.common.urls_api_v1')),
    url(r'^api/v1/mockapi/', include('apps.mockapi.urls_api_v1')),
]

# serve apidoc and other static files in debug mode
# in production mode, the files is strongly recommended to be served
# by professional web server, e.g. the popular lightweight nginx
if settings.DEBUG:
    apidoc_root = os.path.join(settings.PROJECT_ROOT, 'frontend/dist/apidoc')
    media_root = os.path.join(settings.PROJECT_ROOT, 'staticfiles/media')
    urlpatterns += [
        # serve apidoc index page
        url(r'^apidoc/(?:index.html)?$', static.serve,
            kwargs={'document_root': apidoc_root, 'path': 'index.html'}),
        # serve apidoc assets files
        url(r'^apidoc/(?P<path>.+)$', static.serve,
            kwargs={'document_root': apidoc_root}),
        # serve site media files
        url(r'^media/(?P<path>.+)$', static.serve,
            kwargs={'document_root', media_root}),
    ]

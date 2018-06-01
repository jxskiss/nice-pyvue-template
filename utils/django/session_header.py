# Copied from:
# https://github.com/ryanhiebert/django-session-header

from django.middleware import csrf
from django.contrib.sessions import middleware


class SessionMiddleware(middleware.SessionMiddleware):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        bases = (SessionHeaderMixin, self.SessionStore)
        self.SessionStore = type('SessionStore', bases, {})

    def process_request(self, request):
        super().process_request(request)
        session_id = request.META.get(u'HTTP_X_SESSIONID')
        if session_id:
            request.session = self.SessionStore(session_id)
            request.session.csrf_exempt = True

    def process_response(self, request, response):
        resp = super().process_response(request, response)
        if request.session.session_key:
            response['X-SessionID'] = request.session.session_key
        return resp


class CsrfViewMiddleware(csrf.CsrfViewMiddleware):
    def process_view(self, request, *args, **kwargs):
        if not request.session.csrf_exempt:
            return super().process_view(request, *args, **kwargs)


class SessionHeaderMixin(object):
    def __init__(self, session_key=None):
        super().__init__(session_key)
        self.csrf_exempt = False

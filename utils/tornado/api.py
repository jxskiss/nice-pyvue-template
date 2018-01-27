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
    def default(self, obj):
        try:
            return super().default(obj)
        except TypeError:
            # See "Date Time String Format" in the ECMA-262 specification.
            if isinstance(obj, datetime.datetime):
                r = obj.isoformat()
                if obj.microsecond:
                    r = r[:23] + r[26:]
                if r.endswith('+00:00'):
                    r = r[:-6] + 'Z'
                return r
            elif isinstance(obj, datetime.date):
                return obj.isoformat()
            elif isinstance(obj, datetime.time):
                if obj.utcoffset() is not None:  # timezone aware
                    six.raise_from(ValueError(
                        "JSON can't represent timezone-aware times."), None)
                r = obj.isoformat()
                if obj.microsecond:
                    r = r[:12]
                return r
            elif isinstance(obj, datetime.timedelta):
                return self.duration_iso_string(obj)
            elif isinstance(obj, decimal.Decimal):
                return str(obj)
            elif isinstance(obj, uuid.UUID):
                return str(obj)
            else:
                r = self._try_numpy(obj)
                if r is not None:
                    return r
            raise

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

    @staticmethod
    def _try_numpy(obj):
        try:
            # Not all applications use numpy
            import numpy as np
            if isinstance(
                obj, (np.int_, np.intc, np.intp, np.int8, np.int16,
                      np.int32, np.int64, np.uint8, np.uint16,
                      np.uint32, np.uint64)):
                return int(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(
                obj, (np.float_, np.float16, np.float32, np.float64,
                      np.complex_, np.complex32, np.complex64,
                      np.complex128)):
                return float(obj)
            return None
        except ImportError:
            return None


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
        elif isinstance(exc, mock.KeyMissing):
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

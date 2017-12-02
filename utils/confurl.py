# -*- coding:utf-8 -*-
"""
Parse database and email settings from url-style strings.

Copied from the following two projects:
    https://github.com/kennethreitz/dj-database-url
    https://github.com/migonzalvar/dj-email-url

Requirement: Python 2.7+.
"""

import os
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

TRUTHY = ('1', 'y', 'yes', 't', 'true', 'on')


def unquote(value):
    return urlparse.unquote(value) if value else value


class _ConfUrlMixin(object):

    __slots__ = ()

    @classmethod
    def parse(cls, url, scheme='', allow_fragments=True):
        return cls(*urlparse.urlparse(url, scheme, allow_fragments))

    def to(self, target='dict', **kwargs):
        try:
            return getattr(self, 'to_%s' % target.lower())(**kwargs)
        except AttributeError:
            return self

    def to_dict(self):
        return {
            'username': self.username or '',
            'password': self.password or '',
            'host': self.hostname or '',
            'port': self.port or '',
            'path': self.path or '',
            'options': {
                key: values[-1]
                for key, values in urlparse.parse_qs(self.query).items()
            }
        }


class DatabaseUrl(urlparse.ParseResult, _ConfUrlMixin):

    def to_django(self, conn_max_age=0):
        SCHEMES = {
            'postgres': 'django.db.backends.postgresql_psycopg2',
            'postgresql': 'django.db.backends.postgresql_psycopg2',
            'pgsql': 'django.db.backends.postgresql_psycopg2',
            'postgis': 'django.contrib.gis.db.backends.postgis',
            'mysql': 'django.db.backends.mysql',
            'mysql2': 'django.db.backends.mysql',
            'mysqlgis': 'django.contrib.gis.db.backends.mysql',
            'mysql-connector': 'mysql.connector.django',
            'mssql': 'sql_server.pyodbc',
            'spatialite': 'django.contrib.gis.db.backends.spatialite',
            'sqlite': 'django.db.backends.sqlite3',
            'oracle': 'django.db.backends.oracle',
            'oraclegis': 'django.contrib.gis.db.backends.oracle',
            'redshift': 'django_redshift_backend',
        }

        # special case for in memory sqlite db
        if self.scheme == 'sqlite' and (
                self.netloc == ':memory:' or self.path == ''):
            return {
                'ENGINE': SCHEMES['sqlite'],
                'NAME': ':memory:'
            }

        # otherwise parse the url as normal
        path = self.path[1:]
        if '?' in path and not self.query:
            path, query = path.split('?', 2)
        else:
            path, query = path, self.query
        query = urlparse.parse_qs(query)

        # Handle postgres percent-encoded paths.
        hostname = self.hostname or ''
        if '%2f' in hostname.lower():
            # Switch to netloc to avoid lower cased paths
            hostname = self.netloc
            if '@' in hostname:
                hostname = hostname.split('@', 1)[1]
            if ':' in hostname:
                hostname = hostname.split(':', 1)[1]
            hostname = unquote(hostname)

        engine = SCHEMES.get(self.scheme)
        port = self.port
        if self.scheme == 'oracle':
            port = str(port)

        # Pass the query string into OPTIONS.
        options = {}
        for key, values in query.items():
            if self.scheme == 'mysql' and key == 'ssl-ca':
                options['ssl'] = {'ca': values[-1]}
                continue
            options[key] = values[-1]

        # Support for Postgres Schema URLs
        if 'currentSchema' in options and engine in (
            'django.contrib.gis.db.backends.postgis',
            'django.db.backends.postgresql_psycopg2',
            'django_redshift_backend',
        ):
            options['options'] = '-c search_path={0}'.format(
                options.pop('currentSchema'))

        conf = {
            'NAME': unquote(path or ''),
            'USER': unquote(self.username or ''),
            'PASSWORD': unquote(self.password or ''),
            'HOST': hostname,
            'PORT': port or '',
            'CONN_MAX_AGE': conn_max_age,
        }
        if engine:
            conf['ENGINE'] = engine
        if options:
            conf['OPTIONS'] = options

        return conf


def parse_db_url(target=None, url=None, env='DATABASE_URL'):
    if url is None:
        url = os.getenv(env, '')
    if not url:
        raise ValueError('database url is empty')

    url = DatabaseUrl.parse(url)
    return url if not target else url.to(target)


class EmailUrl(urlparse.ParseResult, _ConfUrlMixin):

    def to_django(self):
        SCHEMES = {
            'smtp': 'django.core.mail.backends.smtp.EmailBackend',
            'smtps': 'django.core.mail.backends.smtp.EmailBackend',
            'console': 'django.core.mail.backends.console.EmailBackend',
            'file': 'django.core.mail.backends.filebased.EmailBackend',
            'memory': 'django.core.mail.backends.locmem.EmailBackend',
            'dummy': 'django.core.mail.backends.dummy.EmailBackend'
        }
        # split query strings from path
        path = self.path[1:]
        if '?' in path and not self.query:
            path, query = path.split('?', 2)
        else:
            path, query = path, self.query
        query = urlparse.parse_qs(query)

        conf = {
            'EMAIL_FILE_PATH': path,
            'EMAIL_HOST_USER': unquote(self.username),
            'EMAIL_HOST_PASSWORD': unquote(self.password),
            'EMAIL_HOST': self.hostname,
            'EMAIL_PORT': self.port,
            'EMAIL_USE_SSL': False,
            'EMAIL_USE_TLS': False,
        }
        if self.scheme in SCHEMES:
            conf['EMAIL_BACKEND'] = SCHEMES[self.scheme]
        if self.scheme == 'smtps':
            conf['EMAIL_USE_TLS'] = True

        if 'ssl' in query and query['ssl']:
            if query['ssl'][0].lower() in TRUTHY:
                conf['EMAIL_USE_SSL'] = True
                conf['EMAIL_USE_TLS'] = False
        elif 'tls' in query and query['tls']:
            if query['tls'][0].lower() in TRUTHY:
                conf['EMAIL_USE_SSL'] = False
                conf['EMAIL_USE_TLS'] = True

        return conf


def parse_email_url(target=None, url=None, env='EMAIL_URL'):
    if url is None:
        url = os.getenv(env, '')
    if not url:
        raise ValueError('email url is empty')

    url = EmailUrl.parse(url)
    return url if not target else url.to(target)

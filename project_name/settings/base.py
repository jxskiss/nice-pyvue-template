"""
Django settings for {{ project_name }} project.

For more information on this file, see
https://docs.djangoproject.com/en/{{ docs_version }}/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/{{ docs_version }}/ref/settings/
"""

import sys
import os

from utils.confurl import parse_db_url, parse_email_url

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
DJANGO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(DJANGO_ROOT)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', '{{ secret_key }}')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', 'yes')

ALLOWED_HOSTS = ['*']


# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    'apps.common',
    'apps.mockapi',
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = '{{ project_name }}.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_ROOT, 'templates'),
            os.path.join(PROJECT_ROOT, 'frontend', 'dist'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = '{{ project_name }}.wsgi.application'

LOGIN_URL = '/admin/login/'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

SECRET_DATABASE_URL = os.getenv('SECRET_DATABASE_URL', '')

DATABASES = {
    'default': parse_db_url('django', SECRET_DATABASE_URL),
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = os.getenv('TIMEZONE', 'Asia/Shanghai')

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
# https://warehouse.python.org/project/whitenoise/
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles', 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = []
# frontend dist static files
_fe_dist_static = os.path.join(PROJECT_ROOT, 'frontend', 'dist', 'static')
if os.path.exists(_fe_dist_static):
    STATICFILES_DIRS.append(_fe_dist_static)


# Logging
_env_log_level = os.getenv('LOG_LEVEL')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'tornado': {
            'format': '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d] %(message)s',  # noqa
            'datefmt': '%y%m%d %H:%M:%S',
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s',  # noqa
        },
        'simple': {
            'format': '%(levelname)s %(message)s',
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console_stdout': {
            'level': _env_log_level or 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'tornado',
        },
        'console_debug': {
            'level': _env_log_level or 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'tornado',
        },
        'console_deploy': {
            'level': _env_log_level or 'WARNING',
            'filters': ['require_debug_false'],
            'class': 'logging.StreamHandler',
            'formatter': 'tornado',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        }
    },
    # NOTE:
    #   1. the root logger will be filtered differently according debug mode
    #   2. the messages sent to 'django', 'py.warnings' and other loggers will
    #      be propagated to the root logger, propagation is default behaviour
    # setup root logger to capture all messages from any logger,
    # eg: foreign libraries
    'loggers': {
        '': {
            'handlers': ['console_debug', 'console_deploy'],
            'level': _env_log_level or 'DEBUG',
        },
        'django': {
            'handlers': ['mail_admins'],
            'level': _env_log_level or 'INFO',
        },
    }
}


# Email settings
SECRET_EMAIL_URL = os.getenv('SECRET_EMAIL_URL', '')
# update EMAIL_ BACKEND, HOST, HOST_USER, HOST_PASSWORD, PORT settings
vars().update(parse_email_url('django', SECRET_EMAIL_URL))
# site configuration
EMAIL_SUBJECT_PREFIX = '[{{ project_name }}] '
DEFAULT_FROM_EMAIL = 'no-reply <no-reply@example.com>'
SERVER_EMAIL = 'alert <alert@example.com>'
ADMINS = (
    ('admin', 'admin@example.com'),
)

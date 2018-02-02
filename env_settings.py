# -*- coding:utf-8 -*-
"""
Environment variables settings.

This file also serves as template of un-tracked file .env, run:
    python env_settings.py > .env

When being imported, all variables listed in this file will be checked
from os.environ, an EnvironmentError will be raised if the policy
"_IF_ENV_MISS" is set to "raise" (the default).

"""

import os
import sys
import warnings

# quote sign used in generated template .env file
_QUOTE_SIGN = '\''
# what to do if variable not in environment: raise, warn, ignore
_IF_ENV_MISS = 'raise'
# whether override existing variable from os with values from .env file
_OVERRIDE_IF_EXIST = True
# whether add "export " prefix to template .env file
_USE_PREFIX_EXPORT = True

# all variables parsed from the .env file when being imported
_ALL_PARSED = {}

DEBUG = False
LOG_LEVEL = 'INFO'
TIME_ZONE = 'Asia/Shanghai'

SECRET_DATABASE_URL = 'sqlite:///dev.db'
SECRET_EMAIL_URL = 'smtp://user@domain.com:pass@smtp.example.com:465/?ssl=True'

SECRET_KEY = '{{ secret_key }}'


def _parse(dir_, vars_):
    from utils import dotenv
    if not os.path.exists('.env'):
        warnings.warn(
            '.env file not found in working directory, searching parents',
            UserWarning)
    dotenv.read_dotenv(dotenv.find_dotenv(), override=_OVERRIDE_IF_EXIST)
    absent = []
    for var in dir_:
        if var.isupper() and not var.startswith('_'):
            if var not in os.environ:
                absent.append(var)
            else:
                value = os.getenv(var)
                if isinstance(eval(var), bool):
                    value = value.lower() in ('true', 'yes', 'on')
                _ALL_PARSED[var] = value
    if absent:
        msg = 'miss environment variables: %s' % ', '.join(absent)
        if _IF_ENV_MISS == 'raise':
            raise EnvironmentError(msg)
        elif _IF_ENV_MISS == 'warn':
            warnings.warn(msg, UserWarning)
        else:
            pass
    vars_.update(_ALL_PARSED)


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'check':
        from pprint import pprint
        _parse(dir(), vars())
        pprint(_ALL_PARSED)
        raise SystemExit(0)

    # generate template content for .env file
    print('# See env_settings.py for more details about env variables.')
    for _var in dir():
        if _var.isupper() and not _var.startswith('_'):
            print('{3}{0}={1}{2}{1}'.format(
                _var, _QUOTE_SIGN, str(eval(_var)),
                'export ' if _USE_PREFIX_EXPORT else ''))
else:
    # source and check variables from .env file
    _parse(dir(), vars())

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
import warnings

# quote sign used in generated template .env file
_QUOTE_SIGN = ''

# what to do if variable not in environment: raise, warn, ignore
_IF_ENV_MISS = 'raise'

# whether override existing variable from os with values from .env file
_OVERRIDE_IF_EXIST = True


DEBUG = False
LOG_LEVEL = 'INFO'
TIMEZONE = 'Asia/Shanghai'

SECRET_DATABASE_URL = 'sqlite:///dev.db'
SECRET_EMAIL_URL = 'smtp://user@domain.com:pass@smtp.example.com:465/?ssl=True'

SECRET_KEY = '{{ secret_key }}'


if __name__ == '__main__':
    # generate template content for .env file
    for _var in dir():
        if _var.isupper() and not _var.startswith('_'):
            print('export {0}={1}{2}{1}'.format(
                _var, _QUOTE_SIGN, str(eval(_var))))
else:
    # source and check variables from .env file
    from utils import dotenv
    if not os.path.exists('.env'):
        warnings.warn(
            '.env file not found in working directory, searching parents',
            UserWarning)
    dotenv.read_dotenv(dotenv.find_dotenv(), override=_OVERRIDE_IF_EXIST)
    _values = {}
    for _var in dir():
        if _var.isupper() and not _var.startswith('_'):
            if _var not in os.environ:
                _msg = 'miss environment variable %s' % _var
                if _IF_ENV_MISS == 'raise':
                    raise EnvironmentError(_msg)
                elif _IF_ENV_MISS == 'warn':
                    warnings.warn(_msg, UserWarning)
                else:
                    pass
            else:
                _values[_var] = os.getenv(_var)
    vars().update(_values)

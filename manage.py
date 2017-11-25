#!/usr/bin/env python
import functools
import os
import re
import sys
from utils import dotenv


def _patch_command_startapp(main_func):
    @functools.wraps(main_func)
    def wrapper(*args, **kwargs):
        need_patch = False
        app_name = ''
        if len(sys.argv) >= 3 and sys.argv[1] == 'startapp':
            arguments = [x for x in sys.argv[2:] if not x.startswith('-')]
            if len(arguments) == 1:
                app_name = arguments[0]
                if os.sep not in app_name:
                    need_patch = True
        if not need_patch:
            return main_func(*args, **kwargs)

        # append app directory to command line arguments
        app_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'apps', app_name))
        if not os.path.exists(app_dir):
            os.mkdir(app_dir)
        sys.argv.append(app_dir)
        ret = main_func(*args, **kwargs)
        # fix app name in AppConfig
        app_config_path = os.path.join(app_dir, 'apps.py')
        if os.path.exists(app_config_path):
            with open(os.path.join(app_dir), 'r+') as fd:
                content = fd.read()
                new_content = re.sub(
                    r"name\s*=\s*'{}'".format(app_name),
                    "name = 'apps.{}'".format(app_name),
                    content)
                fd.seek(0)
                fd.write(new_content)
        return ret
    return wrapper


@_patch_command_startapp
def main():
    dotenv.read_dotenv()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ project_name }}.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

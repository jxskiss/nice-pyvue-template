#!/usr/bin/env python
import os
import sys
import dotenv


def main():
    dotenv.read_dotenv()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ project_name }}.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


def _patch_command_start_app():
    """
    Patch command line to start app under apps directory.
    """
    if len(sys.argv) < 3 or sys.argv[1] != 'startapp':
        return
    arguments = [x for x in sys.argv[2:] if not x.startswith('-')]
    if len(arguments) != 1:
        return

    app_name = arguments[0]
    if os.sep in app_name:
        return
    app_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'apps', app_name))
    if not os.path.exists(app_dir):
        os.mkdir(app_dir)
    sys.argv.append(app_dir)


if __name__ == "__main__":
    _patch_command_start_app()
    main()

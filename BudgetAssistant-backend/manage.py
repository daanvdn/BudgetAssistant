#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys



import os
if os.getenv('DEBUG_PYCHARM', 'false').lower() == 'true':
    try:
        print("Debugging in PyCharm")
        import pydevd_pycharm

        pydevd_pycharm.settrace('host.docker.internal', port=29781, stdoutToServer=True, stderrToServer=True)
    except:
        print("PyCharm debugger not available, continuing without it")


def main():


    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pybackend.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

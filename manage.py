#!/usr/bin/env python
"""Django boshqaruv buyruqlari: python manage.py runserver / migrate / test / ..."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sunat.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

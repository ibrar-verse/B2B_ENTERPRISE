#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# -------------------------------------------------------------
# Python 3.14 + Django 5.0 Compatibility Patch for BaseContext
# -------------------------------------------------------------
try:
    from django.template import context as django_context

    def _safe_basecontext_copy(self):
        cls = self.__class__
        duplicate = cls.__new__(cls)
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    django_context.BaseContext.__copy__ = _safe_basecontext_copy
except Exception:
    pass
# -------------------------------------------------------------


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
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
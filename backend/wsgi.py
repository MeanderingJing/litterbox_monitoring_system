"""
WSGI entry point for production servers (gunicorn, etc.).
For production, use `gunicorn wsgi:app` since we have a wsgi.py entry point file.
Without wsgi.py, I would need to use `gunicorn litterlog.api.app:app` instead.
"""

from litterlog.api.app import app

__all__ = ["app"]

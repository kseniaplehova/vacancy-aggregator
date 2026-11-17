"""Настройки для сервера, доступного из интернета."""
import os

from .base import *  # noqa: F401,F403

DEBUG = False
# без ключа и списка адресов сервер не запустится — это намеренно
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
ALLOWED_HOSTS = os.environ["DJANGO_ALLOWED_HOSTS"].split(",")

CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

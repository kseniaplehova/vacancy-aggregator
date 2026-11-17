"""Настройки для разработки на своей машине."""
import os

from .base import *  # noqa: F401,F403

DEBUG = True
# ключ только для локального запуска; на сервере он обязан прийти из окружения
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-development-only")
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

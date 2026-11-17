"""Настройки для разработки на своей машине."""
import os

from .base import *  # noqa: F401,F403

DEBUG = True
# ключ только для локального запуска; на сервере он обязан прийти из окружения
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-development-only-not-for-production-use")
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# обычные адреса локального фронтенда (Create React App и Vite)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

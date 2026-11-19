import os

from .base import *

DEBUG = True
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-development-only-not-for-production-use")
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

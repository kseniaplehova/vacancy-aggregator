from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Пользователь сервиса.

    Своя модель заведена с самого начала: заменить стандартную на свою
    после первых миграций в Django очень трудно, а поля ещё добавятся.
    """

    email = models.EmailField("электронная почта", unique=True)

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

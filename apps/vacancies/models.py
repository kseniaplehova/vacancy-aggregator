from django.conf import settings
from django.db import models


class Vacancy(models.Model):
    source = models.CharField("источник", max_length=64, db_index=True)
    source_id = models.CharField("номер в источнике", max_length=128)
    url = models.URLField("ссылка", max_length=500)
    title = models.CharField("название", max_length=500)
    company = models.CharField("компания", max_length=300, blank=True, null=True)
    city = models.CharField("город", max_length=200, blank=True, null=True)
    salary = models.CharField("зарплата", max_length=200, blank=True, null=True)
    description = models.TextField("описание", blank=True, null=True)
    published = models.CharField("опубликована", max_length=64, blank=True, null=True)
    origin = models.CharField(
        "первоисточник",
        max_length=128,
        blank=True,
        null=True,
        help_text="Площадка, с которой вакансию взял источник-агрегатор.",
    )
    origin_url = models.URLField(
        "ссылка на первоисточник",
        max_length=500,
        blank=True,
        null=True,
        help_text="Адрес этой же вакансии на площадке-первоисточнике.",
    )
    detailed = models.BooleanField(
        "описание полное",
        default=False,
        help_text="Страница вакансии загружена; иначе в описании только фрагмент из списка.",
    )
    search_text = models.TextField(
        "текст для поиска",
        blank=True,
        default="",
        editable=False,
        help_text="Название, компания и описание в нижнем регистре без знаков препинания.",
    )
    duplicate_of = models.ForeignKey(
        "self",
        verbose_name="дубликат вакансии",
        on_delete=models.SET_NULL,
        related_name="duplicates",
        blank=True,
        null=True,
        help_text="Основная запись этой же вакансии из другого источника; пусто, если запись сама основная.",
    )
    first_seen = models.DateTimeField("впервые собрана")
    last_seen = models.DateTimeField("последний раз встречалась")

    class Meta:
        verbose_name = "вакансия"
        verbose_name_plural = "вакансии"
        ordering = ["-last_seen", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["source", "source_id"], name="unique_vacancy_in_source"),
        ]

    def __str__(self):
        return f"{self.title} — {self.company or 'компания не указана'} ({self.source})"


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="пользователь", on_delete=models.CASCADE, related_name="favorites"
    )
    vacancy = models.ForeignKey(
        Vacancy, verbose_name="вакансия", on_delete=models.CASCADE, related_name="favorites"
    )
    created = models.DateTimeField("добавлена", auto_now_add=True)

    class Meta:
        verbose_name = "избранная вакансия"
        verbose_name_plural = "избранные вакансии"
        ordering = ["-created"]
        constraints = [
            models.UniqueConstraint(fields=["user", "vacancy"], name="unique_favorite"),
        ]

    def __str__(self):
        return f"{self.user} → {self.vacancy}"


class SavedSearch(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="пользователь", on_delete=models.CASCADE, related_name="searches"
    )
    name = models.CharField("название", max_length=100)
    query = models.CharField("слова для поиска", max_length=200, blank=True)
    city = models.CharField("город", max_length=200, blank=True)
    source = models.CharField("источник", max_length=64, blank=True)
    created = models.DateTimeField("создан", auto_now_add=True)

    class Meta:
        verbose_name = "сохранённый поиск"
        verbose_name_plural = "сохранённые поиски"
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name} ({self.user})"

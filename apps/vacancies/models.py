from django.db import models


class Vacancy(models.Model):
    """Вакансия, собранная из источника.

    Зарплата и дата публикации хранятся строкой: источники записывают их
    по-разному («от 4 000 BYN», «$1500—4000», «Сегодня»).
    """

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
    first_seen = models.DateTimeField("впервые собрана")
    last_seen = models.DateTimeField("последний раз встречалась")

    class Meta:
        verbose_name = "вакансия"
        verbose_name_plural = "вакансии"
        ordering = ["-last_seen", "-id"]
        constraints = [
            # одна и та же вакансия источника хранится один раз
            models.UniqueConstraint(fields=["source", "source_id"], name="unique_vacancy_in_source"),
        ]

    def __str__(self):
        return f"{self.title} — {self.company or 'компания не указана'} ({self.source})"

from rest_framework import serializers

from apps.vacancies.models import SavedSearch, Vacancy

SNIPPET_LENGTH = 300


class VacancyListSerializer(serializers.ModelSerializer):
    """Вакансия в списке: без полного описания, со всеми источниками, где она встретилась."""

    snippet = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Vacancy
        fields = (
            "id",
            "title",
            "company",
            "city",
            "salary",
            "published",
            "snippet",
            "sources",
            "is_favorite",
            "first_seen",
            "last_seen",
        )

    def get_snippet(self, vacancy) -> str:
        text = " ".join((vacancy.description or "").split())
        return text if len(text) <= SNIPPET_LENGTH else text[:SNIPPET_LENGTH].rsplit(" ", 1)[0] + "…"

    def get_sources(self, vacancy) -> list[dict]:
        """Основная запись и её дубликаты: где ещё опубликована эта вакансия."""
        records = [vacancy, *vacancy.duplicates.all()]
        return [{"source": record.source, "url": record.url} for record in records]

    def get_is_favorite(self, vacancy) -> bool:
        # номера избранных вакансий пользователя кладёт в контекст представление — одним запросом на весь список
        return vacancy.pk in self.context.get("favorite_ids", ())


class VacancySerializer(VacancyListSerializer):
    """Вакансия целиком."""

    class Meta(VacancyListSerializer.Meta):
        fields = (*VacancyListSerializer.Meta.fields, "description")


class SavedSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedSearch
        fields = ("id", "name", "query", "city", "source", "created")
        read_only_fields = ("created",)

    def validate(self, data):
        values = {**{f: getattr(self.instance, f, "") for f in ("query", "city", "source")}, **data}
        if not any(values[field] for field in ("query", "city", "source")):
            raise serializers.ValidationError("Задайте хотя бы один критерий: слова для поиска, город или источник.")
        return data

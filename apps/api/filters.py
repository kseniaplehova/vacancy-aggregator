from django.db.models import Q
from django_filters import rest_framework as filters

from apps.vacancies.models import Vacancy
from apps.vacancies.services.dedup.normalize import normalize


class VacancyFilter(filters.FilterSet):
    q = filters.CharFilter(method="filter_q", label="слова для поиска")
    city = filters.CharFilter(field_name="city", lookup_expr="exact")
    source = filters.CharFilter(method="filter_source", label="источник")
    has_salary = filters.BooleanFilter(method="filter_has_salary", label="указана зарплата")

    class Meta:
        model = Vacancy
        fields = ["q", "city", "source", "has_salary"]

    def filter_q(self, queryset, name, value):
        # ищем по заранее нормализованному тексту: SQLite не умеет сравнивать
        # кириллицу без учёта регистра, а так «Аналитик» и «аналитик» совпадают
        for word in normalize(value).split():
            queryset = queryset.filter(search_text__contains=word)
        return queryset

    def filter_source(self, queryset, name, value):
        # вакансия подходит, если в этом источнике есть она сама или её дубликат
        return queryset.filter(Q(source=value) | Q(duplicates__source=value)).distinct()

    def filter_has_salary(self, queryset, name, value):
        missing = Q(salary__isnull=True) | Q(salary="")
        return queryset.exclude(missing) if value else queryset.filter(missing)

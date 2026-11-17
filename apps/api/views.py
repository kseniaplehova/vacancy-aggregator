from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.vacancies.models import Favorite, SavedSearch, Vacancy

from .filters import VacancyFilter
from .pagination import VacancyPagination
from .serializers import SavedSearchSerializer, VacancyListSerializer, VacancySerializer


def main_vacancies():
    """Вакансии без дубликатов: каждая группа представлена основной записью."""
    return Vacancy.objects.filter(duplicate_of__isnull=True).prefetch_related("duplicates")


class FavoriteContextMixin:
    """Передаёт сериализатору номера избранных вакансий текущего пользователя."""

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            context["favorite_ids"] = set(Favorite.objects.filter(user=user).values_list("vacancy_id", flat=True))
        return context


class VacancyViewSet(FavoriteContextMixin, viewsets.ReadOnlyModelViewSet):
    """Список вакансий с поиском и отбором, одна вакансия, добавление в избранное."""

    queryset = main_vacancies()
    pagination_class = VacancyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = VacancyFilter
    ordering_fields = ("first_seen", "last_seen")
    ordering = ("-first_seen", "-id")

    def get_serializer_class(self):
        return VacancySerializer if self.action == "retrieve" else VacancyListSerializer

    @action(detail=True, methods=["post", "delete"], permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        vacancy = self.get_object()
        if request.method == "POST":
            _, created = Favorite.objects.get_or_create(user=request.user, vacancy=vacancy)
            return Response(status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        Favorite.objects.filter(user=request.user, vacancy=vacancy).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(FavoriteContextMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Избранные вакансии текущего пользователя, сначала добавленные последними."""

    serializer_class = VacancyListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = VacancyPagination

    def get_queryset(self):
        return (
            Vacancy.objects.filter(favorites__user=self.request.user)
            .prefetch_related("duplicates")
            .order_by("-favorites__created")
        )


class SavedSearchViewSet(viewsets.ModelViewSet):
    """Сохранённые критерии отбора текущего пользователя."""

    serializer_class = SavedSearchSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = None

    def get_queryset(self):
        return SavedSearch.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FilterOptionsView(APIView):
    """Значения для выпадающих списков: источники и города с числом вакансий."""

    def get(self, request):
        vacancies = main_vacancies()

        def options(field):
            rows = vacancies.exclude(**{f"{field}__isnull": True}).exclude(**{field: ""})
            rows = rows.values(field).annotate(count=Count("id")).order_by("-count", field)
            return [{"value": row[field], "count": row["count"]} for row in rows]

        return Response(
            {
                "total": vacancies.count(),
                "duplicates_merged": Vacancy.objects.filter(duplicate_of__isnull=False).count(),
                "sources": options("source"),
                "cities": options("city"),
            }
        )

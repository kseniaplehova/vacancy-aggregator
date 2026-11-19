from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FavoriteViewSet, FilterOptionsView, SavedSearchViewSet, VacancyViewSet

router = DefaultRouter()
router.register("vacancies", VacancyViewSet, basename="vacancy")
router.register("favorites", FavoriteViewSet, basename="favorite")
router.register("searches", SavedSearchViewSet, basename="search")

urlpatterns = [
    path("v1/filters/", FilterOptionsView.as_view(), name="filters"),
    path("v1/", include(router.urls)),
    path("v1/auth/", include("djoser.urls")),
    path("v1/auth/", include("djoser.urls.jwt")),
]

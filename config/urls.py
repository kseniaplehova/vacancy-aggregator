from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.api.urls")),
    # все остальные адреса отдают страницу фронтенда: переходы между экранами он делает сам
    re_path(r"^(?!api/|admin/|static/).*$", TemplateView.as_view(template_name="index.html"), name="frontend"),
]

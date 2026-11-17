from django.contrib import admin

from .models import Vacancy


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "city", "salary", "source", "origin", "last_seen")
    list_filter = ("source", "origin", "city")
    search_fields = ("title", "company", "description")
    readonly_fields = ("first_seen", "last_seen")

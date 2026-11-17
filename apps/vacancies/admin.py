from django.contrib import admin

from .models import Favorite, SavedSearch, Vacancy


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "city", "salary", "source", "origin", "duplicate_of", "last_seen")
    list_filter = ("source", "origin", "detailed")
    search_fields = ("title", "company", "description")
    readonly_fields = ("first_seen", "last_seen")
    raw_id_fields = ("duplicate_of",)
    list_select_related = ("duplicate_of",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "vacancy", "created")
    raw_id_fields = ("vacancy",)


@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "query", "city", "source", "created")

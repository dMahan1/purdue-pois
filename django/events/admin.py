from django.contrib import admin

from .models import Building, Category, Event


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "latitude", "longitude"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "building", "room", "start_time", "end_time"]
    list_filter = ["category", "building"]
    search_fields = ["title", "description", "organizer"]

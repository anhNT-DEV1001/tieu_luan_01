from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "email", "role", "status", "city", "country")
    list_filter = ("role", "status", "country")
    search_fields = ("full_name", "email", "phone")

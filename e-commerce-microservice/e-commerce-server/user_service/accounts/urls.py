from django.urls import path

from .views import user_collection, user_detail, user_login, user_summary

urlpatterns = [
    path("", user_collection),
    path("login/", user_login),
    path("summary/", user_summary),
    path("<int:user_id>/", user_detail),
]

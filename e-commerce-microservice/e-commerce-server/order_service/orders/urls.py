from django.urls import path

from .views import order_collection, order_detail, order_summary

urlpatterns = [
    path("", order_collection),
    path("summary/", order_summary),
    path("<int:order_id>/", order_detail),
]

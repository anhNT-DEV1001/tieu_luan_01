from django.urls import path

from .views import product_collection, product_detail, product_summary

urlpatterns = [
    path("", product_collection),
    path("summary/", product_summary),
    path("<int:product_id>/", product_detail),
]

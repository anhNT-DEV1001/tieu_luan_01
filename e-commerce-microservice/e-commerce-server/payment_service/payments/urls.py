from django.urls import path

from .views import payment_collection, payment_detail, payment_summary

urlpatterns = [
    path("", payment_collection),
    path("summary/", payment_summary),
    path("<int:payment_id>/", payment_detail),
]

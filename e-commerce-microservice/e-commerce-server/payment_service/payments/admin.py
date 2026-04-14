from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order_id", "payer_name", "amount", "method", "status", "transaction_code")
    list_filter = ("method", "status")
    search_fields = ("payer_name", "transaction_code")

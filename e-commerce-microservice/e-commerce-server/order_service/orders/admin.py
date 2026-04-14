from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "customer_name", "status", "total_amount", "shipping_city")
    list_filter = ("status", "shipping_city")
    search_fields = ("customer_name", "customer_email")
    inlines = [OrderItemInline]

from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "sku", "name", "category", "brand", "price", "discount_price", "stock_quantity", "status")
    list_filter = ("category", "brand", "status")
    search_fields = ("sku", "name", "slug")

from django.db import models


class Product(models.Model):
    class ProductStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        DRAFT = "draft", "Draft"
        ARCHIVED = "archived", "Archived"

    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=120)
    brand = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="VND")
    stock_quantity = models.PositiveIntegerField(default=0)
    safety_stock = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    weight_grams = models.PositiveIntegerField(default=0)
    dimensions = models.JSONField(default=dict, blank=True)
    color = models.CharField(max_length=64, blank=True)
    material = models.CharField(max_length=120, blank=True)
    size = models.CharField(max_length=32, blank=True)
    origin_country = models.CharField(max_length=120, blank=True)
    warranty_months = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    attributes = models.JSONField(default=dict, blank=True)
    thumbnail_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=ProductStatus.choices, default=ProductStatus.ACTIVE)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def current_price(self):
        return self.discount_price or self.price

    def to_dict(self):
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "slug": self.slug,
            "category": self.category,
            "brand": self.brand,
            "price": float(self.price),
            "discount_price": float(self.discount_price) if self.discount_price is not None else None,
            "current_price": float(self.current_price()),
            "currency": self.currency,
            "stock_quantity": self.stock_quantity,
            "safety_stock": self.safety_stock,
            "rating": float(self.rating),
            "weight_grams": self.weight_grams,
            "dimensions": self.dimensions,
            "color": self.color,
            "material": self.material,
            "size": self.size,
            "origin_country": self.origin_country,
            "warranty_months": self.warranty_months,
            "description": self.description,
            "tags": self.tags,
            "attributes": self.attributes,
            "thumbnail_url": self.thumbnail_url,
            "status": self.status,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

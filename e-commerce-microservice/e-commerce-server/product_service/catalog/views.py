import json

from django.db.models import Avg, Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Product


def _json_body(request):
    return json.loads(request.body.decode("utf-8") or "{}")


@csrf_exempt
def product_collection(request):
    if request.method == "GET":
        queryset = Product.objects.all().order_by("id")
        category = request.GET.get("category")
        if category:
            queryset = queryset.filter(category__iexact=category)
        return JsonResponse({"count": queryset.count(), "results": [product.to_dict() for product in queryset]})

    if request.method == "POST":
        payload = _json_body(request)
        product = Product.objects.create(**payload)
        return JsonResponse(product.to_dict(), status=201)

    return JsonResponse({"error": "Method not allowed"}, status=405)


def product_detail(_request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    return JsonResponse(product.to_dict())


def product_summary(_request):
    aggregate = Product.objects.aggregate(total=Count("id"), avg_rating=Avg("rating"))
    return JsonResponse(
        {
            "service": "product_service",
            "total_products": aggregate["total"] or 0,
            "average_rating": float(aggregate["avg_rating"] or 0),
            "categories": sorted(Product.objects.values_list("category", flat=True).distinct()),
        }
    )

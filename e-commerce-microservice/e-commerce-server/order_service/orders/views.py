import json
from decimal import Decimal

import requests
from django.conf import settings
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Order, OrderItem


def _json_body(request):
    return json.loads(request.body.decode("utf-8") or "{}")


def _fetch_user(user_id):
    response = requests.get(f"{settings.USER_SERVICE_URL}{user_id}/", timeout=15)
    response.raise_for_status()
    return response.json()


def _fetch_product(product_id):
    response = requests.get(f"{settings.PRODUCT_SERVICE_URL}{product_id}/", timeout=15)
    response.raise_for_status()
    return response.json()


@csrf_exempt
def order_collection(request):
    if request.method == "GET":
        queryset = Order.objects.all().order_by("-id")
        status = request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return JsonResponse({"count": queryset.count(), "results": [order.to_dict() for order in queryset]})

    if request.method == "POST":
        payload = _json_body(request)
        try:
            user = _fetch_user(payload["user_id"])
        except requests.RequestException as exc:
            return JsonResponse({"error": "Could not validate user", "detail": str(exc)}, status=502)

        items_payload = payload.get("items", [])
        if not items_payload:
            return JsonResponse({"error": "Order requires at least one item"}, status=400)

        hydrated_items = []
        subtotal = Decimal("0")
        for item in items_payload:
            try:
                product = _fetch_product(item["product_id"])
            except requests.RequestException as exc:
                return JsonResponse({"error": "Could not validate product", "detail": str(exc)}, status=502)

            quantity = int(item["quantity"])
            unit_price = Decimal(str(product["current_price"]))
            line_total = unit_price * quantity
            subtotal += line_total
            hydrated_items.append(
                {
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "sku": product["sku"],
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "line_total": line_total,
                    "product_snapshot": product,
                }
            )

        shipping_fee = Decimal(str(payload.get("shipping_fee", 30000)))
        order = Order.objects.create(
            user_id=user["id"],
            customer_name=user["full_name"],
            customer_email=user["email"],
            shipping_address=payload.get("shipping_address") or user.get("address") or "Demo address",
            shipping_city=payload.get("shipping_city") or user.get("city") or "Ho Chi Minh City",
            status=payload.get("status", Order.OrderStatus.PENDING),
            subtotal_amount=subtotal,
            shipping_fee=shipping_fee,
            total_amount=subtotal + shipping_fee,
            notes=payload.get("notes", ""),
            metadata=payload.get("metadata", {}),
        )
        OrderItem.objects.bulk_create([OrderItem(order=order, **item) for item in hydrated_items])
        return JsonResponse(order.to_dict(), status=201)

    return JsonResponse({"error": "Method not allowed"}, status=405)


def order_detail(_request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)
    return JsonResponse(order.to_dict())


def order_summary(_request):
    aggregate = Order.objects.aggregate(total_orders=Count("id"), revenue=Sum("total_amount"))
    top_customer = (
        Order.objects.values("user_id", "customer_name", "customer_email")
        .annotate(order_count=Count("id"), total_spent=Sum("total_amount"))
        .order_by("-order_count", "-total_spent", "customer_name")
        .first()
    )
    best_selling_product = (
        OrderItem.objects.values("product_id", "product_name", "sku")
        .annotate(total_quantity=Sum("quantity"), total_revenue=Sum("line_total"))
        .order_by("-total_quantity", "-total_revenue", "product_name")
        .first()
    )
    return JsonResponse(
        {
            "service": "order_service",
            "total_orders": aggregate["total_orders"] or 0,
            "gross_revenue": float(aggregate["revenue"] or 0),
            "top_customer": (
                {
                    "user_id": top_customer["user_id"],
                    "customer_name": top_customer["customer_name"],
                    "customer_email": top_customer["customer_email"],
                    "order_count": top_customer["order_count"] or 0,
                    "total_spent": float(top_customer["total_spent"] or 0),
                }
                if top_customer
                else None
            ),
            "best_selling_product": (
                {
                    "product_id": best_selling_product["product_id"],
                    "product_name": best_selling_product["product_name"],
                    "sku": best_selling_product["sku"],
                    "total_quantity": best_selling_product["total_quantity"] or 0,
                    "total_revenue": float(best_selling_product["total_revenue"] or 0),
                }
                if best_selling_product
                else None
            ),
        }
    )

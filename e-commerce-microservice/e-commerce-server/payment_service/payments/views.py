import json
import uuid

import requests
from django.conf import settings
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Payment


def _json_body(request):
    return json.loads(request.body.decode("utf-8") or "{}")


def _fetch_order(order_id):
    response = requests.get(f"{settings.ORDER_SERVICE_URL}{order_id}/", timeout=15)
    response.raise_for_status()
    return response.json()


@csrf_exempt
def payment_collection(request):
    if request.method == "GET":
        queryset = Payment.objects.all().order_by("-id")
        method = request.GET.get("method")
        if method:
            queryset = queryset.filter(method=method)
        return JsonResponse({"count": queryset.count(), "results": [payment.to_dict() for payment in queryset]})

    if request.method == "POST":
        payload = _json_body(request)
        try:
            order = _fetch_order(payload["order_id"])
        except requests.RequestException as exc:
            return JsonResponse({"error": "Could not validate order", "detail": str(exc)}, status=502)

        status = payload.get("status", Payment.PaymentStatus.PAID)
        payment = Payment.objects.create(
            order_id=order["id"],
            payer_name=payload.get("payer_name", order["customer_name"]),
            amount=payload.get("amount", order["total_amount"]),
            currency=payload.get("currency", "VND"),
            method=payload.get("method", Payment.PaymentMethod.MOMO),
            status=status,
            transaction_code=payload.get("transaction_code", uuid.uuid4().hex[:16].upper()),
            gateway_response={
                "order_status": order["status"],
                "captured_by": "demo-payment-service",
                "source": payload.get("source", "manual"),
            },
            paid_at=timezone.now() if status == Payment.PaymentStatus.PAID else None,
        )
        return JsonResponse(payment.to_dict(), status=201)

    return JsonResponse({"error": "Method not allowed"}, status=405)


def payment_detail(_request, payment_id):
    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        return JsonResponse({"error": "Payment not found"}, status=404)
    return JsonResponse(payment.to_dict())


def payment_summary(_request):
    aggregate = Payment.objects.aggregate(total_payments=Count("id"), paid_value=Sum("amount"))
    return JsonResponse(
        {
            "service": "payment_service",
            "total_payments": aggregate["total_payments"] or 0,
            "processed_amount": float(aggregate["paid_value"] or 0),
        }
    )

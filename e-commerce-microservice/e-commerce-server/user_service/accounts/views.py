import json

from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import UserProfile


def _json_body(request):
    return json.loads(request.body.decode("utf-8") or "{}")


@csrf_exempt
def user_collection(request):
    if request.method == "GET":
        role = request.GET.get("role")
        queryset = UserProfile.objects.all().order_by("id")
        if role:
            queryset = queryset.filter(role=role)
        return JsonResponse({"count": queryset.count(), "results": [user.to_dict() for user in queryset]})

    if request.method == "POST":
        payload = _json_body(request)
        user = UserProfile.objects.create(
            full_name=payload["full_name"],
            email=payload["email"],
            phone=payload.get("phone", ""),
            role=payload.get("role", UserProfile.Role.CUSTOMER),
            status=payload.get("status", UserProfile.Status.ACTIVE),
            loyalty_points=payload.get("loyalty_points", 0),
            address=payload.get("address", ""),
            city=payload.get("city", ""),
            country=payload.get("country", "Vietnam"),
            avatar_url=payload.get("avatar_url", ""),
            metadata=payload.get("metadata", {}),
        )
        return JsonResponse(user.to_dict(), status=201)

    return JsonResponse({"error": "Method not allowed"}, status=405)


def user_detail(_request, user_id):
    try:
        user = UserProfile.objects.get(id=user_id)
    except UserProfile.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    return JsonResponse(user.to_dict())


def user_summary(_request):
    roles = {
        row["role"]: row["count"]
        for row in UserProfile.objects.values("role").annotate(count=Count("id")).order_by("role")
    }
    return JsonResponse({"service": "user_service", "total_users": UserProfile.objects.count(), "roles": roles})


@csrf_exempt
def user_login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    payload = _json_body(request)
    email = (payload.get("email") or "").strip().lower()
    if not email:
        return JsonResponse({"error": "Email is required"}, status=400)

    try:
        user = UserProfile.objects.get(email__iexact=email)
    except UserProfile.DoesNotExist:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    if user.status != UserProfile.Status.ACTIVE:
        return JsonResponse({"error": "User is inactive"}, status=403)

    return JsonResponse({"user": user.to_dict()})

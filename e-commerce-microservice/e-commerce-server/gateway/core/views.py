from urllib.parse import urljoin

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def proxy_router(request, service, subpath=""):
    if service not in settings.SERVICE_URLS:
        return JsonResponse({"error": f"Unsupported service '{service}'"}, status=404)

    upstream = urljoin(settings.SERVICE_URLS[service], subpath.lstrip("/"))
    if request.META.get("QUERY_STRING"):
        upstream = f"{upstream}?{request.META['QUERY_STRING']}"

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length"}
    }

    try:
        response = requests.request(
            method=request.method,
            url=upstream,
            headers=headers,
            data=request.body or None,
            timeout=20,
        )
    except requests.RequestException as exc:
        return JsonResponse(
            {"error": "Upstream service unavailable", "detail": str(exc), "service": service},
            status=502,
        )

    django_response = HttpResponse(
        content=response.content,
        status=response.status_code,
        content_type=response.headers.get("Content-Type", "application/json"),
    )
    for header, value in response.headers.items():
        if header.lower() not in {"content-encoding", "transfer-encoding", "connection"}:
            django_response[header] = value
    return django_response


def healthcheck(_request):
    return JsonResponse(
        {
            "service": "gateway",
            "status": "ok",
            "upstreams": settings.SERVICE_URLS,
        }
    )

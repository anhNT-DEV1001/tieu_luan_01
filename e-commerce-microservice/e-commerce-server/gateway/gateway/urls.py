from django.contrib import admin
from django.urls import path
from core.views import healthcheck, proxy_router

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', healthcheck),
    path('api/<str:service>', proxy_router),
    path('api/<str:service>/', proxy_router),
    path('api/<str:service>/<path:subpath>', proxy_router),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, ShiftViewSet

router = DefaultRouter()
# Register shifts FIRST - must come before empty route
router.register(r'shifts', ShiftViewSet, basename='shift')  # /api/orders/shifts/
router.register(r'', OrderViewSet, basename='order')  # /api/orders/

urlpatterns = [
    path('', include(router.urls)),
]

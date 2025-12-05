from rest_framework import generics
from rest_framework.permissions import AllowAny
from orders.models import Order
from orders.serializers import OrderShowcaseSerializer


class ShowcaseListView(generics.ListAPIView):
    """
    Public API endpoint for showcase.
    Returns only delivered orders to display finished work.
    No authentication required.
    """
    permission_classes = [AllowAny]
    serializer_class = OrderShowcaseSerializer
    queryset = Order.objects.filter(status='DELIVERED').order_by('-delivered_at')
    
    def get_queryset(self):
        """Only return orders with images for better showcase"""
        queryset = super().get_queryset()
        # Optionally filter to only show orders with images
        if self.request.query_params.get('with_image', 'false').lower() == 'true':
            queryset = queryset.exclude(image='')
        return queryset

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import NotFound, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum
from django.utils import timezone

from .models import Order, Shift
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderUpdateStatusSerializer,
    ShiftSerializer
)
from .permissions import IsManager, CanUpdateOrder, CanDeleteOrder


class ShiftViewSet(viewsets.ModelViewSet):
    """ViewSet for managing work shifts"""
    queryset = Shift.objects.all().order_by('-opened_at')  # Newest first
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated, IsManager]
    http_method_names = ['get', 'post']
    ordering_fields = ['opened_at', 'closed_at']
    ordering = ['-opened_at']
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def current(self, request):
        """Get current active shift"""
        shift = Shift.objects.filter(is_active=True).first()
        if shift:
            return Response(ShiftSerializer(shift).data)
        raise NotFound('No active shift')
    
    @action(detail=False, methods=['post'])
    def open_new(self, request):
        """Open a new shift"""
        # Close any active shifts first
        active_shifts = Shift.objects.filter(is_active=True)
        for shift in active_shifts:
            self._close_shift(shift, request.user)
        
        # Create new shift with explicit zero values
        shift = Shift.objects.create(
            opened_by=request.user,
            is_active=True,
            total_orders_delivered=0,
            total_revenue=0.0
        )
        return Response(ShiftSerializer(shift).data, status=201)
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a shift and calculate stats"""
        shift = self.get_object()
        if not shift.is_active:
            raise ValidationError('Shift already closed')
        
        self._close_shift(shift, request.user)
        
        # Return detailed summary
        return Response({
            'shift': ShiftSerializer(shift).data,
            'summary': {
                'total_orders_delivered': shift.total_orders_delivered,
                'total_revenue': float(shift.total_revenue),
                'message': f'Shift closed! Delivered {shift.total_orders_delivered} orders. Total revenue: ${shift.total_revenue}'
            }
        })
    
    def _close_shift(self, shift, user):
        """Helper to close shift and calculate delivered orders/revenue"""
        shift.closed_at = timezone.now()
        shift.closed_by = user
        shift.is_active = False
        
        # Get delivered orders in this shift timeframe
        delivered_orders = Order.objects.filter(
            status='DELIVERED',
            delivered_at__gte=shift.opened_at,
            delivered_at__lte=shift.closed_at
        )
        
        # Calculate stats
        shift.total_orders_delivered = delivered_orders.count()
        total_rev = delivered_orders.aggregate(Sum('price'))['price__sum']
        shift.total_revenue = total_rev if total_rev else 0
        
        # Link orders to this shift
        delivered_orders.update(delivered_in_shift=shift)
        
        shift.save()
    
    @action(detail=True, methods=['get'])
    def delivered_orders(self, request, pk=None):
        """Get all orders delivered during this shift"""
        shift = self.get_object()
        
        if shift.is_active:
            # For active shifts, get orders delivered since shift opened
            orders = Order.objects.filter(
                status='DELIVERED',
                delivered_at__gte=shift.opened_at,
                delivered_at__isnull=False
            )
        else:
            # For closed shifts, get orders linked to this shift or within timeframe
            orders = Order.objects.filter(
                status='DELIVERED',
                delivered_at__gte=shift.opened_at,
                delivered_at__lte=shift.closed_at
            )
        
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Order model with role-based permissions.
    
    - List/Retrieve: Managers and Workers
    - Create: Managers and Workers
    - Update: Managers (all fields), Workers (status only)
    - Delete: Managers only
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, CanUpdateOrder, CanDeleteOrder]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'delivered_at']
    search_fields = ['customer_name', 'customer_phone', 'order_details']
    ordering_fields = ['created_at', 'updated_at', 'price', 'delivered_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'update_status':
            return OrderUpdateStatusSerializer
        return OrderSerializer
    
    def perform_create(self, serializer):
        """Set the created_by field to the current user"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        """
        Custom action for updating only the order status.
        Allows workers to update status without touching other fields.
        """
        order = self.get_object()
        serializer = OrderUpdateStatusSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return full order data
        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsManager])
    def statistics(self, request):
        """
        Get order statistics (Manager only).
        Returns counts by status.
        """
        stats = {
            'total': Order.objects.count(),
            'by_status': dict(
                Order.objects.values('status')
                .annotate(count=Count('id'))
                .values_list('status', 'count')),
            'delivered_this_month': Order.objects.filter(
                delivered_at__month=request.query_params.get('month'),
                delivered_at__year=request.query_params.get('year')
            ).count() if request.query_params.get('month') and request.query_params.get('year')
            else None
        }
        
        return Response(stats)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def track(self, request, pk=None):
        """
        Public endpoint for customers to track their order.
        """
        try:
            order = self.get_object()
        except:
             # If get_object fails due to permission (though specific perms usually run after)
             # or not found. 
             # Since class has IsAuthenticated, get_object might fail if we rely on standard lookup
             # BUT permission_classes on action overrides class permissions for the check.
             # However, get_object() uses the queryset which is fine.
             # Let's double check if we need to manually fetch to avoid auth issues if filtering happens.
             # Standard get_object() is usually fine if queryset is generic.
             # Our queryset is Order.objects.all().
             
             # Actually safer to just do a direct fetch to be sure
             try:
                 order = Order.objects.get(pk=pk)
             except Order.DoesNotExist:
                 raise NotFound('Order not found')

        return Response({
            'id': order.id,
            'status': order.status,
            'status_display': order.get_status_display(),
            'customer_name': order.customer_name,
            'order_details': order.order_details,
            'created_at': order.created_at,
            'delivered_at': order.delivered_at
        })

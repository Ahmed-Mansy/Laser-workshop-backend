from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from datetime import datetime, date
from orders.models import Order
from orders.serializers import OrderSerializer
from orders.permissions import IsManager


class DailyReportView(APIView):
    """
    API endpoint for daily financial report.
    Manager only. Returns delivered orders (revenue) and created orders (status) for a specific date.
    
    Query params:
    - date: YYYY-MM-DD format (defaults to today)
    """
    permission_classes = [IsAuthenticated, IsManager]
    
    def get(self, request):
        # Get date from query params or default to today
        date_str = request.query_params.get('date')
        if date_str:
            try:
                report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=400
                )
        else:
            report_date = date.today()
        
        # 1. Financials: Based on DELIVERED orders on this date
        delivered_orders = Order.objects.filter(
            status='DELIVERED',
            delivered_at__date=report_date
        )
        
        total_delivered_count = delivered_orders.count()
        total_revenue = delivered_orders.aggregate(total=Sum('price'))['total'] or 0
        
        # 2. Operations: Based on CREATED orders on this date
        # This shows the current status of all orders that originated on this day
        created_orders = Order.objects.filter(
            created_at__date=report_date
        )
        
        # Calculate status breakdown
        status_counts = created_orders.values('status').annotate(count=Count('id'))
        orders_by_status = {item['status']: item['count'] for item in status_counts}
        
        # Ensure all statuses are present with 0 if not found
        for status, _ in Order.STATUS_CHOICES:
            if status not in orders_by_status:
                orders_by_status[status] = 0

        # Serialize delivered orders for detailed view if needed
        # (Though UI mainly uses aggregates)
        order_data = OrderSerializer(delivered_orders, many=True).data
        
        return Response({
            'date': report_date,
            'total_orders': total_delivered_count,
            'total_revenue': float(total_revenue),
            'average_order_value': float(total_revenue / total_delivered_count) if total_delivered_count > 0 else 0,
            'orders_by_status': orders_by_status,
            'orders': order_data
        })


class MonthlyReportView(APIView):
    """
    API endpoint for monthly financial report.
    Manager only. Returns delivered orders (revenue) and created orders (status) for a specific month.
    
    Query params:
    - year: Year (defaults to current year)
    - month: Month 1-12 (defaults to current month)
    """
    permission_classes = [IsAuthenticated, IsManager]
    
    def get(self, request):
        # Get year and month from query params or default to current
        try:
            year = int(request.query_params.get('year', date.today().year))
            month = int(request.query_params.get('month', date.today().month))
            
            if not (1 <= month <= 12):
                return Response(
                    {'error': 'Month must be between 1 and 12'},
                    status=400
                )
        except ValueError:
            return Response(
                {'error': 'Invalid year or month format'},
                status=400
            )
        
        # 1. Financials: Based on DELIVERED orders in this month
        delivered_orders = Order.objects.filter(
            status='DELIVERED',
            delivered_at__year=year,
            delivered_at__month=month
        )
        
        total_delivered_count = delivered_orders.count()
        total_revenue = delivered_orders.aggregate(total=Sum('price'))['total'] or 0
        
        # 2. Operations: Based on CREATED orders in this month
        created_orders = Order.objects.filter(
            created_at__year=year,
            created_at__month=month
        )
        
        # Calculate status breakdown
        status_counts = created_orders.values('status').annotate(count=Count('id'))
        orders_by_status = {item['status']: item['count'] for item in status_counts}
        
        # Ensure all statuses are present
        for status, _ in Order.STATUS_CHOICES:
            if status not in orders_by_status:
                orders_by_status[status] = 0
        
        # 3. Daily Breakdown (Financials)
        # Shows revenue trend over the month
        daily_breakdown = {}
        for order in delivered_orders:
            day = order.delivered_at.day
            if day not in daily_breakdown:
                daily_breakdown[day] = {'count': 0, 'revenue': 0}
            daily_breakdown[day]['count'] += 1
            daily_breakdown[day]['revenue'] += float(order.price) if order.price else 0
        
        # Convert to list format
        daily_data = [
            {
                'day': day,
                'count': data['count'],
                'revenue': data['revenue']
            }
            for day, data in sorted(daily_breakdown.items())
        ]
        
        return Response({
            'year': year,
            'month': month,
            'total_orders': total_delivered_count,
            'total_revenue': float(total_revenue),
            'average_order_value': float(total_revenue / total_delivered_count) if total_delivered_count > 0 else 0,
            'orders_by_status': orders_by_status,
            'daily_breakdown': daily_data,
        })

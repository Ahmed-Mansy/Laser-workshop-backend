from django.urls import path
from .views import DailyReportView, MonthlyReportView

urlpatterns = [
    path('daily/', DailyReportView.as_view(), name='daily_report'),
    path('monthly/', MonthlyReportView.as_view(), name='monthly_report'),
]

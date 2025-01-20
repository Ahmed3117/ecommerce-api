from django.urls import path
from .views import ProductPerformanceView, CategoryPerformanceView, SalesTrendsView


urlpatterns = [
    path('products/', ProductPerformanceView.as_view(), name='product-analytics'),
    path('categories/', CategoryPerformanceView.as_view(), name='category-analytics'),
    path('sales/', SalesTrendsView.as_view(), name='sales-trends'),
]
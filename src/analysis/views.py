# views.py
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum, Count, Avg, F, Q, FloatField, Case, When, BooleanField, Subquery, OuterRef, IntegerField, ExpressionWrapper
from django.utils import timezone
from datetime import datetime
from django.db.models.functions import Coalesce
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear,TruncDate
from analysis.serializers import CategoryAnalyticsSerializer, InventoryAlertSerializer, ProductAnalyticsSerializer, SalesTrendSerializer
from products.models import Category, Discount, Pill, Product
from rest_framework import generics, filters
from rest_framework.response import Response
from django_filters import rest_framework as django_filters
from datetime import datetime

class ProductAnalyticsFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='date_added', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='date_added', lookup_expr='lte')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.NumberFilter(field_name='category__id')
    
    class Meta:
        model = Product
        fields = ['category', 'brand', 'start_date', 'end_date', 'min_price', 'max_price']


class ProductAnalyticsFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='date_added', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='date_added', lookup_expr='lte')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.NumberFilter(field_name='category__id')
    
    class Meta:
        model = Product
        fields = ['category', 'brand', 'start_date', 'end_date', 'min_price', 'max_price']

class ProductPerformanceView(generics.ListAPIView):
    serializer_class = ProductAnalyticsSerializer
    filter_backends = [django_filters.DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = ProductAnalyticsFilter
    ordering_fields = ['total_sold', 'revenue', 'average_rating', 'total_available', 'price']
    search_fields = ['name']
    
    def get_queryset(self):
        queryset = Product.objects.all()
        
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        low_stock_threshold = self.request.query_params.get('low_stock_threshold')

        queryset = queryset.annotate(
            total_available=Coalesce(Sum('availabilities__quantity'), 0),
            total_added=Coalesce(
                Sum('availabilities__quantity',
                    filter=Q(availabilities__date_added__range=(start_date, end_date))
                    if start_date and end_date else Q()
                ), 0),
            total_sold=Coalesce(
                Sum('sales__quantity',
                    filter=Q(sales__date_sold__range=(start_date, end_date))
                    if start_date and end_date else Q()
                ), 0),
            revenue=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F('sales__quantity') * F('sales__price_at_sale'),
                        output_field=FloatField()
                    ),
                    filter=Q(sales__date_sold__range=(start_date, end_date))
                    if start_date and end_date else Q()
                ), 
                0.0,
                output_field=FloatField()
            ),
            average_rating=Coalesce(Avg('ratings__star_number'), 0.0),
            total_ratings=Count('ratings'),
            has_discount=Case(
                When(discounts__discount_end__gte=timezone.now(), then=True),
                default=False,
                output_field=BooleanField()
            ),
            current_discount=Coalesce(
                Subquery(
                    Discount.objects.filter(
                        Q(product=OuterRef('pk')) | Q(category=OuterRef('category')),
                        discount_start__lte=timezone.now(),
                        discount_end__gte=timezone.now()
                    ).values('discount')[:1]
                ), 0.0
            ),
            price_after_discount=Case(
                When(
                    current_discount__gt=0,
                    then=F('price') * (1 - F('current_discount') / 100)
                ),
                default=F('price'),
                output_field=FloatField()
            )
        )

        if low_stock_threshold:
            queryset = queryset.filter(total_available__lte=low_stock_threshold)

        return queryset




class CategoryPerformanceView(generics.ListAPIView):
    serializer_class = CategoryAnalyticsSerializer
    
    def get_queryset(self):
        return Category.objects.annotate(
            total_products=Count('products'),
            total_sales=Coalesce(
                Sum('products__sales__quantity'),
                0,
                output_field=IntegerField()
            ),
            revenue=Coalesce(
                Sum(F('products__sales__quantity') * F('products__sales__price_at_sale')),
                0,
                output_field=FloatField()
            )
        )


class SalesTrendsView(generics.ListAPIView):
    serializer_class = SalesTrendSerializer
    
    def get_queryset(self):
        # Get date parameters
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        # Base queryset for delivered orders
        queryset = Pill.objects.filter(status='d')
        
        # If dates provided, filter by date range
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                queryset = queryset.filter(date_added__range=(start, end))
                date_start = start.date()
                date_end = end.date()
            except ValueError:
                return []
        else:
            # For all-time totals, get the date of first and last order
            first_order = queryset.order_by('date_added').first()
            last_order = queryset.order_by('-date_added').first()
            
            if first_order and last_order:
                date_start = first_order.date_added.date()
                date_end = last_order.date_added.date()
            else:
                # If no orders exist
                today = timezone.now().date()
                date_start = today
                date_end = today

        # Get aggregated data
        results = queryset.aggregate(
            total_sales=Count('id'),
            revenue=Sum(
                ExpressionWrapper(
                    F('items__quantity') * F('items__product__price'),
                    output_field=FloatField()
                )
            )
        )
        
        # Add date range to results
        results['start_date'] = date_start
        results['end_date'] = date_end
        
        # Handle None values
        results['total_sales'] = results['total_sales'] or 0
        results['revenue'] = results['revenue'] or 0.0
        
        return [results]


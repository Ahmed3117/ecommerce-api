
from .models import Product
from django_filters import rest_framework as filters
from django.db.models import Q, F, FloatField, Case, When
from django.utils import timezone
from .models import Product, CouponDiscount

class ProductFilter(filters.FilterSet):
    price_min = filters.NumberFilter(method='filter_by_discounted_price_min')
    price_max = filters.NumberFilter(method='filter_by_discounted_price_max')
    color = filters.CharFilter(method='filter_by_color')
    size = filters.CharFilter(method='filter_by_size')

    class Meta:
        model = Product
        fields = ['category', 'sub_category', 'brand']

    def filter_by_discounted_price_min(self, queryset, name, value):
        now = timezone.now()

        # Annotate the queryset with product discounts
        queryset = queryset.annotate(
            product_discount_price=Case(
                When(
                    Q(discounts__discount_start__lte=now) &
                    Q(discounts__discount_end__gte=now),
                    then=F('price') * (1 - F('discounts__discount') / 100)
                ),
                default=F('price'),
                output_field=FloatField()
            ),
            category_discount_price=Case(
                When(
                    Q(category__discounts__discount_start__lte=now) &
                    Q(category__discounts__discount_end__gte=now),
                    then=F('price') * (1 - F('category__discounts__discount') / 100)
                ),
                default=F('price'),
                output_field=FloatField()
            )
        ).annotate(
            final_price=Case(
                When(
                    product_discount_price__lt=F('category_discount_price'),
                    then=F('product_discount_price')
                ),
                default=F('category_discount_price'),
                output_field=FloatField()
            )
        )

        return queryset.filter(final_price__gte=value).distinct()

    def filter_by_discounted_price_max(self, queryset, name, value):
        now = timezone.now()

        # Same annotation logic as above
        queryset = queryset.annotate(
            product_discount_price=Case(
                When(
                    Q(discounts__discount_start__lte=now) &
                    Q(discounts__discount_end__gte=now),
                    then=F('price') * (1 - F('discounts__discount') / 100)
                ),
                default=F('price'),
                output_field=FloatField()
            ),
            category_discount_price=Case(
                When(
                    Q(category__discounts__discount_start__lte=now) &
                    Q(category__discounts__discount_end__gte=now),
                    then=F('price') * (1 - F('category__discounts__discount') / 100)
                ),
                default=F('price'),
                output_field=FloatField()
            )
        ).annotate(
            final_price=Case(
                When(
                    product_discount_price__lt=F('category_discount_price'),
                    then=F('product_discount_price')
                ),
                default=F('category_discount_price'),
                output_field=FloatField()
            )
        )

        return queryset.filter(final_price__lte=value).distinct()

    def filter_by_color(self, queryset, name, value):
        return queryset.filter(availabilities__color__name__iexact=value).distinct()

    def filter_by_size(self, queryset, name, value):
        return queryset.filter(availabilities__size__iexact=value).distinct()

class CouponDiscountFilter(filters.FilterSet):
    available = filters.BooleanFilter(method='filter_available')

    class Meta:
        model = CouponDiscount
        fields = ['available']

    def filter_available(self, queryset, name, value):
        now = timezone.now()
        if value:
            return queryset.filter(
                available_use_times__gt=0,
                coupon_start__lte=now,
                coupon_end__gte=now
            )
        return queryset

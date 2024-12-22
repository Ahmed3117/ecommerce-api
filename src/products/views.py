
from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, SubCategory, Brand, Product
from .serializers import (
    CategorySerializer,
    SubCategorySerializer,
    BrandSerializer,
    ProductSerializer,
)

# 1. Get Categories
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None  # Optional: Disable pagination if not needed

# 2. Get SubCategories
class SubCategoryListView(generics.ListAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    pagination_class = None

# 3. Get Brands
class BrandListView(generics.ListAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    pagination_class = None

# 4. Get Products with Filtering
class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category__name', 'sub_category__name', 'brand__name']
    search_fields = ['name', 'category__name', 'brand__name', 'description']

# 5. Get Last 10 Products
class Last10ProductsListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.all().order_by('-date_added')[:10]

# 6. Get Product Details
class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'id'  # Default is 'pk', but you can use 'id' if needed
from django.urls import path
from .views import (
    CategoryListView,
    SubCategoryListView,
    BrandListView,
    ProductListView,
    Last10ProductsListView,
    ProductDetailView,
)

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('subcategories/', SubCategoryListView.as_view(), name='subcategory-list'),
    path('brands/', BrandListView.as_view(), name='brand-list'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/last10/', Last10ProductsListView.as_view(), name='last-10-products'),
    path('products/<int:id>/', ProductDetailView.as_view(), name='product-detail'),
]
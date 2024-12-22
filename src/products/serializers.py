from rest_framework import serializers
from .models import Category, SubCategory, Brand, Product, ProductImage, ProductAvailability, Rating, Color

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = '__all__'

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = '__all__'

class ProductAvailabilitySerializer(serializers.ModelSerializer):
    color = ColorSerializer()

    class Meta:
        model = ProductAvailability
        fields = '__all__'

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    price_after_product_discount = serializers.SerializerMethodField()
    price_after_category_discount = serializers.SerializerMethodField()
    has_discount = serializers.SerializerMethodField()
    main_image = serializers.SerializerMethodField()
    number_of_ratings = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    available_colors = serializers.SerializerMethodField()
    available_sizes = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'sub_category', 'brand', 'price', 'description', 'date_added',
            'price_after_product_discount', 'price_after_category_discount', 'has_discount',
            'main_image', 'images', 'number_of_ratings', 'average_rating', 'total_quantity',
            'available_colors', 'available_sizes',
        ]

    def get_price_after_product_discount(self, obj):
        return obj.price_after_product_discount()

    def get_price_after_category_discount(self, obj):
        return obj.price_after_category_discount()

    def get_has_discount(self, obj):
        return obj.has_discount()

    def get_main_image(self, obj):
        return obj.main_image().image.url if obj.main_image() else None

    def get_number_of_ratings(self, obj):
        return obj.number_of_ratings()

    def get_average_rating(self, obj):
        return obj.average_rating()

    def get_total_quantity(self, obj):
        return obj.total_quantity()

    def get_available_colors(self, obj):
        return obj.available_colors()

    def get_available_sizes(self, obj):
        return obj.available_sizes()



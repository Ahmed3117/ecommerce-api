from rest_framework import serializers
from .models import Category, CouponDiscount, PillAddress, Shipping, SubCategory, Brand, Product, ProductImage, ProductAvailability, Rating, Color,Pill

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
    color = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all())

    class Meta:
        model = ProductAvailability
        fields = ['id', 'product', 'size', 'color', 'quantity']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['color'] = ColorSerializer(instance.color).data
        return representation

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['id', 'product', 'user', 'star_number', 'review', 'date_added']
        read_only_fields = ['date_added', 'user']

    def validate(self, data):
        if data.get('star_number') < 1 or data.get('star_number') > 5:
            raise serializers.ValidationError("Star number must be between 1 and 5.")
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    discounted_price = serializers.SerializerMethodField()
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
            'discounted_price',  'has_discount',
            'main_image', 'images', 'number_of_ratings', 'average_rating', 'total_quantity',
            'available_colors', 'available_sizes',
        ]

    def get_discounted_price(self, obj):
        return obj.discounted_price()

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

class PillCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pill
        fields = ['id', 'items', 'status', 'date_added', 'paid', 'pill_number']
        read_only_fields = ['status', 'date_added', 'paid', 'pill_number']

class CouponCodeField(serializers.Field):
    """
    Custom field to handle coupon code as a string and convert it to the CouponDiscount instance.
    """
    def to_internal_value(self, data):
        # Look up the CouponDiscount instance by coupon code
        try:
            return CouponDiscount.objects.get(coupon=data)
        except CouponDiscount.DoesNotExist:
            raise serializers.ValidationError("Coupon does not exist.")

    def to_representation(self, value):
        # Return the coupon code for representation
        return value.coupon

class PillCouponApplySerializer(serializers.ModelSerializer):
    coupon = CouponCodeField()  # Use the custom field for coupon

    class Meta:
        model = Pill
        fields = ['id', 'coupon', 'price_without_coupons', 'coupon_discount', 'price_after_coupon_discount', 'final_price']
        read_only_fields = ['id', 'price_without_coupons', 'coupon_discount', 'price_after_coupon_discount', 'final_price']

class PillAddressCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PillAddress
        fields = ['id', 'pill', 'name', 'email', 'phone', 'address', 'government','pay_method']
        read_only_fields = ['id', 'pill']

class CouponDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponDiscount
        fields = ['coupon', 'discount_value', 'coupon_start', 'coupon_end', 'available_use_times']

class PillAddressSerializer(serializers.ModelSerializer):
    government = serializers.SerializerMethodField()

    class Meta:
        model = PillAddress
        fields = ['name', 'email', 'phone', 'address', 'government']

    def get_government(self, obj):
        return obj.get_government_display()

class ShippingSerializer(serializers.ModelSerializer):
    government_name = serializers.SerializerMethodField()

    class Meta:
        model = Shipping
        fields = ['government', 'government_name', 'shipping_price']

    def get_government_name(self, obj):
        return obj.get_government_display()

class PillDetailSerializer(serializers.ModelSerializer):
    items = ProductSerializer(many=True, read_only=True)  
    coupon = CouponDiscountSerializer(read_only=True)  
    pilladdress = PillAddressSerializer(read_only=True)  
    shipping_price = serializers.SerializerMethodField()  
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Pill
        fields = [
            'id', 'items', 'status', 'status_display', 'date_added', 'paid', 'coupon', 'pilladdress',
            'price_without_coupons', 'coupon_discount', 'price_after_coupon_discount',
            'shipping_price', 'final_price', 'pill_number'
        ]
        read_only_fields = ['date_added', 'paid', 'price_without_coupons', 'coupon_discount', 'price_after_coupon_discount', 'shipping_price', 'final_price', 'pill_number']

    def get_shipping_price(self, obj):
        """
        Calculate the shipping price dynamically based on the PillAddress.
        """
        return obj.shipping_price()

    def get_status_display(self, obj):
        return obj.get_status_display()





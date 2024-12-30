from rest_framework import serializers
from collections import defaultdict

from accounts.models import User
from .models import Category, CouponDiscount, PillAddress, PillItem, Shipping, SubCategory, Brand, Product, ProductImage, ProductAvailability, Rating, Color,Pill



class SubCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()  # Add a field for the category name

    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category', 'category_name']  # Include category_name in the response

    def get_category_name(self, obj):
        # Return the name of the related category
        return obj.category.name
    
class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)  # Nested subcategories

    class Meta:
        model = Category
        fields = ['id', 'name', 'subcategories']

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
    color = serializers.PrimaryKeyRelatedField(
        queryset=Color.objects.all(),
        allow_null=True,  # Allow null values
        required=False    # Make the field optional
    )
    size = serializers.CharField(
        allow_null=True,  # Allow null values
        required=False    # Make the field optional
    )
    product_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductAvailability
        fields = ['id', 'product', 'product_name', 'size', 'color', 'quantity']

    def get_product_name(self, obj):
        return obj.product.name

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Only serialize color if it exists
        if instance.color:
            representation['color'] = ColorSerializer(instance.color).data
        else:
            representation['color'] = None  # Explicitly set color to null if it doesn't exist
        return representation

class ProductAvailabilityBreifedSerializer(serializers.Serializer):
    size = serializers.CharField()
    color = serializers.CharField()
    quantity = serializers.IntegerField()


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


class ProductImageBulkUploadSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    images = serializers.ListField(
        child=serializers.ImageField(),  # Each item in the list is an ImageField
        allow_empty=False,  # Ensure at least one image is provided
    )


from collections import defaultdict

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    availabilities = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()
    has_discount = serializers.SerializerMethodField()
    main_image = serializers.SerializerMethodField()
    number_of_ratings = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    available_colors = serializers.SerializerMethodField()
    available_sizes = serializers.SerializerMethodField()

    # Add direct fields for category, sub_category, and brand
    category_id = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    sub_category_id = serializers.SerializerMethodField()
    sub_category_name = serializers.SerializerMethodField()
    brand_id = serializers.SerializerMethodField()
    brand_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category_id', 'category_name', 'sub_category_id', 'sub_category_name',
            'brand_id', 'brand_name', 'price', 'description', 'date_added', 'discounted_price',
            'has_discount', 'main_image', 'images', 'number_of_ratings', 'average_rating',
            'total_quantity', 'available_colors', 'available_sizes', 'availabilities',
        ]

    def get_category_id(self, obj):
        return obj.category.id if obj.category else None

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_sub_category_id(self, obj):
        return obj.sub_category.id if obj.sub_category else None

    def get_sub_category_name(self, obj):
        return obj.sub_category.name if obj.sub_category else None

    def get_brand_id(self, obj):
        return obj.brand.id if obj.brand else None

    def get_brand_name(self, obj):
        return obj.brand.name if obj.brand else None

    def get_availabilities(self, obj):
        # Group availabilities by size and color, and sum the quantities
        grouped_availabilities = defaultdict(int)
        for availability in obj.availabilities.all():
            key = (availability.size, availability.color.id if availability.color else None, availability.color.name if availability.color else None)
            grouped_availabilities[key] += availability.quantity

        # Convert the grouped data into the desired format
        result = [
            {
                "size": size,
                "color_id": color_id,  # Include color_id
                "color": color_name,   # Include color name
                "quantity": quantity
            }
            for (size, color_id, color_name), quantity in grouped_availabilities.items()
        ]
        return result

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

class ProductBreifedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name']

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
        fields = ['id','government', 'government_name', 'shipping_price']

    def get_government_name(self, obj):
        return obj.get_government_display()

class PillItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    color = ColorSerializer(read_only=True)

    class Meta:
        model = PillItem
        fields = ['id', 'product', 'quantity', 'size', 'color']

class PillItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PillItem
        fields = ['product', 'quantity', 'size', 'color']

class PillCreateSerializer(serializers.ModelSerializer):
    items = PillItemCreateSerializer(many=True)  # Nested serializer for PillItem
    user_name = serializers.SerializerMethodField() 
    user_username = serializers.SerializerMethodField()  
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)  # Make user optional

    class Meta:
        model = Pill
        fields = ['id', 'user', 'user_name', 'user_username', 'items', 'status', 'date_added', 'paid']
        read_only_fields = ['status', 'date_added', 'paid']

    def get_user_name(self, obj):
        return obj.user.name

    def get_user_username(self, obj):
        return obj.user.username

    def create(self, validated_data):
        # Extract the nested items data
        items_data = validated_data.pop('items')
        # Create the Pill instance
        pill = Pill.objects.create(**validated_data)
        # Create PillItem instances and add them to the Pill
        for item_data in items_data:
            pill_item = PillItem.objects.create(**item_data)  # Create PillItem without passing 'pill'
            pill.items.add(pill_item)  # Associate the PillItem with the Pill
        return pill
    
    
    
    
class PillDetailSerializer(serializers.ModelSerializer):
    items = PillItemSerializer(many=True, read_only=True)  # Updated to use PillItemSerializer
    coupon = CouponDiscountSerializer(read_only=True)
    pilladdress = PillAddressSerializer(read_only=True)
    shipping_price = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField() 
    user_username = serializers.SerializerMethodField()

    class Meta:
        model = Pill
        fields = [
            'id', 'user_name', 'user_username', 'items', 'status', 'status_display', 'date_added', 'paid', 'coupon', 'pilladdress',
            'price_without_coupons', 'coupon_discount', 'price_after_coupon_discount',
            'shipping_price', 'final_price'
        ]
        read_only_fields = ['date_added', 'paid', 'price_without_coupons', 'coupon_discount', 'price_after_coupon_discount', 'shipping_price', 'final_price']

    def get_user_name(self, obj):
        return obj.user.name

    def get_user_username(self, obj):
        return obj.user.username
    
    def get_shipping_price(self, obj):
        """
        Calculate the shipping price dynamically based on the PillAddress.
        """
        return obj.shipping_price()

    def get_status_display(self, obj):
        return obj.get_status_display()



from django.db.models import Count, Sum, F
from rest_framework import serializers

from products.models import LovedProduct, Pill, Product
from products.serializers import LovedProductSerializer, PillDetailSerializer
from .models import User, UserAddress

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'name', 'is_staff', 'is_superuser')
        extra_kwargs = {
            'is_staff': {'read_only': True},
            'is_superuser': {'read_only': True},
            'email': {'required': False, 'allow_null': True, 'allow_blank': True},  # Make email optional
        }

    def create(self, validated_data):
        # Use .get() with default None for email since it can be optional
        email = validated_data.get('email', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=email,
            password=validated_data['password'],
            name=validated_data.get('name', ''),
            is_staff=validated_data.get('is_staff', False),
            is_superuser=validated_data.get('is_superuser', False),
        )
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    new_password = serializers.CharField()


class UserAddressSerializer(serializers.ModelSerializer):
    government = serializers.SerializerMethodField()

    class Meta:
        model = UserAddress
        fields = ['id', 'name', 'email', 'phone', 'address', 'government', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_government(self, obj):
        return obj.get_government_display()

    def validate(self, data):
        # Ensure only one default address per user
        if data.get('is_default', False):
            UserAddress.objects.filter(user=self.context['request'].user, is_default=True).update(is_default=False)
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    addresses = UserAddressSerializer(many=True, read_only=True)
    pills = serializers.SerializerMethodField()
    loved_products = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    favorite_category = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'name',
            'addresses', 'pills', 'loved_products',
            'total_spent', 'favorite_category'
        ]

    def get_pills(self, obj):
        pills = Pill.objects.filter(user=obj).order_by('-date_added')[:10]
        return PillDetailSerializer(pills, many=True).data

    def get_loved_products(self, obj):
        loved_products = LovedProduct.objects.filter(user=obj).order_by('-created_at')[:10]
        return LovedProductSerializer(loved_products, many=True).data

    def get_total_spent(self, obj):
        return Pill.objects.filter(
            user=obj,
            status='d'
        ).annotate(
            total_price=Sum(F('items__quantity') * F('items__product__price'))
        ).aggregate(total_spent=Sum('total_price'))['total_spent'] or 0

    def get_favorite_category(self, obj):
        favorite = Product.objects.filter(
            sales__pill__user=obj
        ).values(
            'category__name'
        ).annotate(
            count=Count('category')
        ).order_by('-count').first()
        return favorite['category__name'] if favorite else None



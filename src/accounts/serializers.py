from rest_framework import serializers
from .models import User

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

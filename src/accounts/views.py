from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random
from .serializers import UserSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer
from .models import User

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def signin(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.check_password(password):
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    refresh = RefreshToken.for_user(user)
    serializer = UserSerializer(user)
    
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': serializer.data
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save()
            
            send_mail(
                'Password Reset OTP',
                f'Your OTP for password reset is: {otp}',
                'from@example.com',
                [email],
                fail_silently=False,
            )
            return Response({'message': 'OTP sent to your email'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']
        
        try:
            user = User.objects.get(email=email, otp=otp)
            if user.otp_created_at < timezone.now() - timedelta(minutes=10):
                return Response({'error': 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.otp = None
            user.otp_created_at = None
            user.save()
            
            return Response({'message': 'Password reset successful'})
        except User.DoesNotExist:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

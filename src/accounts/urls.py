from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
app_name="accounts"

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('password-reset/', views.request_password_reset, name='password_reset'),
    path('password-reset/confirm/', views.reset_password_confirm, name='password_reset_confirm'),
]

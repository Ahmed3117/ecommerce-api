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
    path('update-profile/', views.UpdateUserProfile.as_view(), name='update-profile'),
    path('get-profile/', views.GetUserProfile.as_view(), name='get-profile'),
    #-----------------Admin--------------------------#
    path('create-admin-user/', views.create_admin_user, name='create-admin-user'),
    path('users/', views.UserListView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', views.UserRetrieveUpdateDestroyView.as_view(), name='user-retrieve-update-destroy'),
]

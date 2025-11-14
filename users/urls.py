from django.urls import path
from .views import UserListView, RegisterUserView
from .auth_views import CustomLoginView


urlpatterns = [
    path('', UserListView.as_view(), name='users'),
    path('register/', RegisterUserView.as_view(), name='register_user'),
    path('login/', CustomLoginView.as_view(), name='custom_login'),
]
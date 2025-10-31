from django.urls import path
from .views import ItemsView


urlpatterns = [
        path('', ItemsView.as_view(), name='items'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('get-response/', views.get_response, name='get_response'),
    path('', views.home, name='home') 
]


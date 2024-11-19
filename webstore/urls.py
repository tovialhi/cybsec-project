"""
URL configuration for project1 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from .views import addItemView, checkoutView, filterView, homePageView, cartView, ordersView, removeItemView, signupView, newitemView, loginView
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', homePageView, name='home'),
    path('signup/', signupView, name='signup'),
    path('login/', loginView, name='login'),
    path('logout/', LogoutView.as_view(next_page='/')),
    path('cart/', cartView, name='cart'),
    path('add/', addItemView, name='addItem'),
    path('remove/', removeItemView, name='removeItem'),
    path('checkout/', checkoutView, name='checkout'),
    path('orders/', ordersView, name='checkout'),
    path('newitem/', newitemView, name='newitem'),
    path('filter/', filterView, name='filter'),
]

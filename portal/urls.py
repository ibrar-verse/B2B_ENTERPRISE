from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.portal_register, name='portal-register'),
    path('login/', views.portal_login, name='portal-login'),
    path('logout/', views.portal_logout, name='portal-logout'),
    
    # Portals
    path('portal/', views.portal_home, name='portal-home'),
    path('catalog/', views.buyer_catalog, name='buyer-catalog'),
    path('orders/', views.buyer_orders, name='buyer-orders'),
    path('vendor/dashboard/', views.vendor_dashboard, name='vendor-dashboard'),
    path('vendor/wallet/', views.vendor_wallet, name='vendor-wallet'),
]
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_view, name='portal-home'),
    path('login/', views.portal_login, name='portal-login'),
    path('logout/', views.portal_logout, name='portal-logout'),
    path('register/', views.register_view, name='portal-register'),
    path('register/buyer/', views.register_buyer_view, name='register-buyer'),
    path('register/vendor/', views.register_vendor_view, name='register-vendor'),

    path('catalog/', views.buyer_catalog, name='buyer-catalog'),
    path('catalog/search/', views.buyer_search, name='buyer-search'),
    path('orders/', views.buyer_orders, name='buyer-orders'),
    path('orders/<int:order_id>/', views.buyer_order_detail, name='buyer-order-detail'),
    path('checkout/<int:product_id>/', views.quick_checkout, name='quick-checkout'),

    path('orders/<int:order_id>/pay/', views.execute_order_payment_htmx, name='htmx-order-pay'),
    path('orders/<int:order_id>/settle/', views.settle_escrow_htmx, name='htmx-order-settle'),
    path('orders/<int:order_id>/refund/', views.dispute_refund_htmx, name='htmx-order-refund'),

    path('vendor/dashboard/', views.vendor_dashboard, name='vendor-dashboard'),
    path('vendor/wallet/', views.vendor_wallet, name='vendor-wallet'),
    path('vendor/payout/', views.vendor_payout, name='vendor-payout'),
]
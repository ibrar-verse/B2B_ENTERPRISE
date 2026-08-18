from django.urls import path
from . import views

# Fallback alias in case views.py defines `home` or `home_view`
home_func = getattr(views, 'home_view', getattr(views, 'home', None))

urlpatterns = [
    # Public & Auth
    path('', home_func, name='home'),
    path('portal/', getattr(views, 'portal_home', home_func), name='portal-home'),
    path('login/', views.portal_login, name='portal-login'),
    path('logout/', views.portal_logout, name='portal-logout'),
    path('register/', views.portal_register, name='portal-register'),
    path('register/buyer/', views.portal_register, name='register-buyer'),
    path('register/vendor/', views.portal_register, name='register-vendor'),

    # Buyer Portal
    path('catalog/', views.buyer_catalog, name='buyer-catalog'),
    path('catalog/search/', getattr(views, 'buyer_search', views.buyer_catalog), name='buyer-search'),
    path('orders/', views.buyer_orders, name='buyer-orders'),
    path('orders/<int:order_id>/', getattr(views, 'buyer_order_detail', getattr(views, 'order_detail', None)), name='buyer-order-detail'),
    path('orders/<int:order_id>/view/', getattr(views, 'buyer_order_detail', getattr(views, 'order_detail', None)), name='order-detail'),
    path('orders/<int:order_id>/pay/', views.execute_order_payment_htmx, name='htmx-order-pay'),
    path('orders/<int:order_id>/settle/', views.settle_escrow_htmx, name='htmx-order-settle'),
    path('orders/<int:order_id>/refund/', getattr(views, 'dispute_refund_htmx', None), name='htmx-order-refund'),
    path('checkout/<int:product_id>/', getattr(views, 'quick_checkout', getattr(views, 'create_checkout_order', None)), name='quick-checkout'),
    path('checkout-order/<int:product_id>/', getattr(views, 'quick_checkout', getattr(views, 'create_checkout_order', None)), name='checkout-order'),

    # Vendor Portal
    path('vendor/dashboard/', views.vendor_dashboard, name='vendor-dashboard'),
    path('vendor/wallet/', views.vendor_wallet, name='vendor-wallet'),
    path('vendor/payout/', getattr(views, 'vendor_payout', None), name='vendor-payout'),
]
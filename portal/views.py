from decimal import Decimal
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.http import Http404
from django.db.models import Q
from django.utils.text import slugify

from apps.organizations.models import Organization, UserProfile
from apps.orders.models import Order, Product
from .forms import RegistrationForm, LoginForm


def _get_user_organization(user):
    """Helper to retrieve the user's organization via UserProfile or direct relation."""
    if hasattr(user, 'profile') and user.profile.organization:
        return user.profile.organization
    if hasattr(user, 'organization') and user.organization:
        return user.organization
    return None


def _get_user_role(user):
    """Helper to retrieve the user's role."""
    if hasattr(user, 'profile') and user.profile.role:
        return user.profile.role
    if hasattr(user, 'role'):
        return user.role
    return 'BUYER'


# ==========================================
# AUTHENTICATION VIEWS
# ==========================================

def home_view(request):
    if request.user.is_authenticated:
        return redirect('portal-home')
    return render(request, 'portal/home.html')


def portal_register(request):
    if request.user.is_authenticated:
        return redirect('portal-home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            org_name = form.cleaned_data['organization_name']
            role = form.cleaned_data['role']

            if User.objects.filter(username=username).exists():
                form.add_error('username', 'This username is already taken.')
                return render(request, 'auth/register.html', {'form': form})

            # 1. Create User
            user = User.objects.create_user(username=username, email=email, password=password)

            # 2. Create Organization & Profile
            slug = slugify(org_name) or f"org-{uuid.uuid4().hex[:6]}"
            if Organization.objects.filter(slug=slug).exists():
                slug = f"{slug}-{uuid.uuid4().hex[:4]}"

            org = Organization.objects.create(name=org_name, slug=slug, org_type=role)
            UserProfile.objects.create(user=user, organization=org, role=role)

            # 3. Log In Immediately
            login(request, user)

            if role == 'VENDOR':
                return redirect('vendor-dashboard')
            return redirect('buyer-catalog')
    else:
        form = RegistrationForm()

    return render(request, 'auth/register.html', {'form': form})


def portal_login(request):
    if request.user.is_authenticated:
        return redirect('portal-home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                return redirect('portal-home')
            else:
                form.add_error(None, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form, 'login_form': form})


@login_required(login_url='portal-login')
def portal_logout(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect('home')


@login_required(login_url='portal-login')
def portal_home(request):
    role = _get_user_role(request.user)
    if role == 'VENDOR':
        return redirect('vendor-dashboard')
    return redirect('buyer-catalog')


# ==========================================
# BUYER PORTAL VIEWS
# ==========================================

@login_required(login_url='portal-login')
@require_GET
def buyer_catalog(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(is_active=True).select_related('vendor')

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(category__icontains=query) |
            Q(vendor__name__icontains=query)
        )

    context = {
        'products': products,
        'query': query,
        'organization': _get_user_organization(request.user),
    }
    if request.headers.get('HX-Request'):
        return render(request, 'partials/catalog_grid.html', context)
    return render(request, 'buyer/catalog.html', context)


@login_required(login_url='portal-login')
@require_GET
def buyer_search(request):
    return buyer_catalog(request)


@login_required(login_url='portal-login')
@require_GET
def buyer_orders(request):
    org = _get_user_organization(request.user)
    orders = (
        Order.objects.filter(buyer=org).select_related('buyer', 'vendor').order_by('-id')
        if org else Order.objects.none()
    )
    return render(request, 'buyer/orders_list.html', {
        'orders': orders,
        'available_balance': sum((o.total_amount for o in orders if o.status == Order.Status.COMPLETED), Decimal('0.00')),
        'escrow_balance': sum((o.total_amount for o in orders if o.status == Order.Status.PAID), Decimal('0.00')),
        'orders_count': orders.count(),
        'organization': org,
    })


@login_required(login_url='portal-login')
@require_GET
def buyer_order_detail(request, order_id):
    order = get_object_or_404(Order.objects.select_related('buyer', 'vendor'), id=order_id)
    org = _get_user_organization(request.user)
    if not request.user.is_staff and org and order.buyer_id != org.id and order.vendor_id != org.id:
        raise Http404("Order not available.")
    return render(request, 'buyer/order_detail.html', {'order': order})


@login_required(login_url='portal-login')
@require_POST
def quick_checkout(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    buyer_org = _get_user_organization(request.user)

    if buyer_org is None:
        messages.error(request, 'Create or join a buyer organization first.')
        return redirect('portal-register')

    order = Order.objects.create(
        buyer=buyer_org,
        vendor=product.vendor,
        created_by=request.user,
        total_amount=product.unit_price,
        status=Order.Status.APPROVED,
    )
    messages.success(request, f'Order #{order.id} generated for {product.name}. Ready for escrow lock.')
    return redirect('buyer-order-detail', order_id=order.id)


# ==========================================
# HTMX ESCROW ACTIONS
# ==========================================

@login_required(login_url='portal-login')
@require_POST
def execute_order_payment_htmx(request, order_id):
    order = get_object_or_404(Order.objects.select_related('buyer', 'vendor'), id=order_id)
    if order.status != Order.Status.APPROVED:
        return render(request, 'partials/order_status_card.html', {
            'order': order,
            'error_message': 'Only approved orders can be charged.'
        })

    if order.execute_payment(payment_method='JAZZCASH'):
        order.refresh_from_db()
        messages.success(request, f'Escrow locked for Order #{order.id}.')
    else:
        messages.error(request, f'Payment failed for Order #{order.id}. Check microservice logs.')
    return render(request, 'partials/order_status_card.html', {'order': order})


@login_required(login_url='portal-login')
@require_POST
def settle_escrow_htmx(request, order_id):
    order = get_object_or_404(Order.objects.select_related('buyer', 'vendor'), id=order_id)
    if order.status != Order.Status.PAID:
        return render(request, 'partials/order_status_card.html', {
            'order': order,
            'error_message': 'Only paid orders can be settled.'
        })

    if order.complete_order():
        order.refresh_from_db()
        messages.success(request, f'Escrow released for Order #{order.id}.')
    else:
        messages.error(request, f'Settlement failed for Order #{order.id}.')
    return render(request, 'partials/order_status_card.html', {'order': order})


@login_required(login_url='portal-login')
@require_POST
def dispute_refund_htmx(request, order_id):
    order = get_object_or_404(Order.objects.select_related('buyer', 'vendor'), id=order_id)
    reason = request.POST.get('reason') or 'Dispute raised by buyer'
    if order.status != Order.Status.PAID:
        return render(request, 'partials/order_status_card.html', {
            'order': order,
            'error_message': 'Only paid orders can be refunded.'
        })

    refund_ref = order.cancel_and_refund(reason=reason)
    order.refresh_from_db()
    if refund_ref:
        messages.warning(request, f'Order #{order.id} refunded and cancelled.')
    else:
        messages.error(request, f'Refund failed for Order #{order.id}.')
    return render(request, 'partials/order_status_card.html', {'order': order})


# ==========================================
# VENDOR PORTAL VIEWS
# ==========================================

@login_required(login_url='portal-login')
@require_GET
def vendor_dashboard(request):
    org = _get_user_organization(request.user)
    orders = (
        Order.objects.filter(vendor=org).select_related('buyer', 'vendor').order_by('-id')
        if org else Order.objects.none()
    )
    return render(request, 'vendor/dashboard.html', {
        'organization': org,
        'orders': orders,
        'pending_orders': [o for o in orders if o.status in {Order.Status.APPROVED, Order.Status.PAID}],
        'total_volume': sum((o.total_amount for o in orders), Decimal('0.00')),
        'paid_volume': sum((o.total_amount for o in orders if o.status == Order.Status.PAID), Decimal('0.00')),
        'completed_volume': sum((o.total_amount for o in orders if o.status == Order.Status.COMPLETED), Decimal('0.00')),
    })


@login_required(login_url='portal-login')
@require_GET
def vendor_wallet(request):
    org = _get_user_organization(request.user)
    orders = (
        Order.objects.filter(vendor=org).select_related('buyer', 'vendor').order_by('-id')
        if org else Order.objects.none()
    )
    available_balance = sum((o.total_amount for o in orders if o.status == Order.Status.COMPLETED), Decimal('0.00'))
    escrow_balance = sum((o.total_amount for o in orders if o.status == Order.Status.PAID), Decimal('0.00'))

    return render(request, 'vendor/wallet.html', {
        'organization': org,
        'orders': orders,
        'available_balance': available_balance,
        'escrow_balance': escrow_balance,
        'payout_ready': available_balance,
        'orders_count': orders.count(),
    })


@login_required(login_url='portal-login')
@require_http_methods(['GET', 'POST'])
def vendor_payout(request):
    if request.method == 'POST':
        amount = request.POST.get('amount') or '0'
        return render(request, 'vendor/modals/payout_modal.html', {
            'success_message': f'Payout request of PKR {amount} submitted to 1Link gateway.',
        })
    return render(request, 'vendor/modals/payout_modal.html', {})
import uuid
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core.models import User
from apps.orders.models import Order
from apps.organizations.models import Organization

from .forms import BuyerRegistrationForm, VendorRegistrationForm


SAMPLE_PRODUCTS = [
    {
        'id': 1,
        'name': 'Industrial High-Pressure Centrifugal Pump',
        'sku': 'PMP-IND-500X',
        'category': 'Mechanical',
        'vendor_name': 'Atlas Heavy Engineering',
        'unit_price': Decimal('50000.00'),
        'min_order_qty': 1,
    },
    {
        'id': 2,
        'name': 'High-Efficiency 3-Phase Industrial Electric Motor',
        'sku': 'MTR-3PH-400V',
        'category': 'Electrical',
        'vendor_name': 'Siemens Regional Vendor',
        'unit_price': Decimal('75000.00'),
        'min_order_qty': 2,
    },
    {
        'id': 3,
        'name': 'Heavy-Duty Carbon Steel Flange Set (DN200)',
        'sku': 'FLG-CS-DN200',
        'category': 'Raw Materials',
        'vendor_name': 'Karachi Steel Traders',
        'unit_price': Decimal('12500.00'),
        'min_order_qty': 10,
    },
]


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Work email',
        widget=forms.EmailInput(attrs={
            'class': 'w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-900 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-4 focus:ring-emerald-100',
            'placeholder': 'name@company.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-900 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-4 focus:ring-emerald-100',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        }),
    )


def _organization_slug(name):
    base_slug = slugify(name) or 'organization'
    candidate = base_slug
    while Organization.objects.filter(slug=candidate).exists():
        candidate = f'{base_slug}-{uuid.uuid4().hex[:6]}'
    return candidate


def _current_organization(user):
    if user.is_authenticated and user.organization_id:
        return user.organization
    return None


def _role_home(user):
    if not user.is_authenticated:
        return reverse('portal-home')
    if user.is_staff or getattr(user, 'role', '') == User.Role.ADMIN:
        return reverse('admin:index')
    org = _current_organization(user)
    if org and org.org_type in (Organization.OrgType.VENDOR, Organization.OrgType.BOTH):
        return reverse('vendor-dashboard')
    return reverse('buyer-catalog')


def _create_user_and_org(form, org_type, default_role):
    organization = Organization.objects.create(
        name=form.cleaned_data['company_name'].strip(),
        slug=_organization_slug(form.cleaned_data['company_name']),
        org_type=org_type,
    )
    user = User.objects.create_user(
        username=form.cleaned_data['username'].strip(),
        email=form.cleaned_data['email'].strip().lower(),
        password=form.cleaned_data['password'],
        organization=organization,
        role=default_role,
    )
    return user


def home_view(request):
    return render(request, 'portal/home.html', {
        'login_form': EmailAuthenticationForm(request),
        'registration_success': request.GET.get('registered') == '1',
        'role_home': _role_home(request.user) if request.user.is_authenticated else None,
    })


@require_http_methods(['GET', 'POST'])
def portal_login(request):
    if request.user.is_authenticated:
        return redirect(_role_home(request.user))

    form = EmailAuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, 'Signed in successfully.')
        return redirect(_role_home(form.get_user()))
    return render(request, 'auth/login.html', {'login_form': form})


@login_required
def portal_logout(request):
    logout(request)
    messages.info(request, 'You have been signed out.')
    return redirect('portal-home')


def _render_registration_page(request, form, title, description, organization_type):
    return render(request, 'auth/register.html', {
        'form': form,
        'page_title': title,
        'page_description': description,
        'organization_type': organization_type,
    })


@require_http_methods(['GET', 'POST'])
def register_buyer_view(request):
    if request.user.is_authenticated:
        return redirect(_role_home(request.user))

    form = BuyerRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = _create_user_and_org(form, Organization.OrgType.BUYER, User.Role.PROCUREMENT_OFFICER)
        login(request, user)
        messages.success(request, 'Buyer workspace created successfully.')
        return redirect('buyer-catalog')

    return _render_registration_page(
        request,
        form,
        'Register Buyer Workspace',
        'Create a buyer organization to browse catalog items and lock escrow orders.',
        'BUYER',
    )


@require_http_methods(['GET', 'POST'])
def register_vendor_view(request):
    if request.user.is_authenticated:
        return redirect(_role_home(request.user))

    form = VendorRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = _create_user_and_org(form, Organization.OrgType.VENDOR, User.Role.MANAGER)
        login(request, user)
        messages.success(request, 'Vendor workspace created successfully.')
        return redirect('vendor-dashboard')

    return _render_registration_page(
        request,
        form,
        'Register Vendor Workspace',
        'Create a vendor organization to manage incoming orders and wallet balances.',
        'VENDOR',
    )


@require_GET
def register_view(request):
    return redirect('portal-home')


@login_required
@require_GET
def buyer_catalog(request):
    query = request.GET.get('q', '').strip().lower()
    products = SAMPLE_PRODUCTS
    if query:
        products = [
            product for product in products
            if query in product['name'].lower()
            or query in product['sku'].lower()
            or query in product['category'].lower()
            or query in product['vendor_name'].lower()
        ]

    context = {
        'products': products,
        'query': request.GET.get('q', '').strip(),
    }
    if request.headers.get('HX-Request'):
        return render(request, 'partials/catalog_grid.html', context)
    return render(request, 'buyer/catalog.html', context)


@login_required
@require_GET
def buyer_search(request):
    return buyer_catalog(request)


@login_required
@require_GET
def buyer_orders(request):
    organization = _current_organization(request.user)
    orders = Order.objects.filter(buyer=organization).select_related('buyer', 'vendor').order_by('-id') if organization else Order.objects.none()
    return render(request, 'buyer/orders_list.html', {
        'orders': orders,
        'available_balance': sum((order.total_amount for order in orders if order.status == Order.Status.COMPLETED), Decimal('0.00')),
        'escrow_balance': sum((order.total_amount for order in orders if order.status == Order.Status.PAID), Decimal('0.00')),
        'orders_count': orders.count(),
        'organization': organization,
    })


@login_required
@require_GET
def buyer_order_detail(request, order_id):
    order = get_object_or_404(Order.objects.select_related('buyer', 'vendor'), id=order_id)
    organization = _current_organization(request.user)
    if not request.user.is_staff and organization and order.buyer_id != organization.id and order.vendor_id != organization.id:
        raise Http404('Order not available.')
    return render(request, 'buyer/order_detail.html', {'order': order})


@login_required
@require_POST
def quick_checkout(request, product_id):
    product = next((item for item in SAMPLE_PRODUCTS if item['id'] == product_id), None)
    if product is None:
        raise Http404('Product not found.')

    buyer_org = _current_organization(request.user)
    if buyer_org is None:
        messages.error(request, 'Create or join a buyer organization first.')
        return redirect('register-buyer')

    vendor_org, _ = Organization.objects.get_or_create(
        name=product['vendor_name'],
        defaults={
            'slug': _organization_slug(product['vendor_name']),
            'org_type': Organization.OrgType.VENDOR,
            'is_active': True,
        },
    )

    order = Order.objects.create(
        buyer=buyer_org,
        vendor=vendor_org,
        created_by=request.user,
        total_amount=product['unit_price'],
        status=Order.Status.APPROVED,
    )
    messages.success(request, f'Order #{order.id} created and approved for escrow payment.')
    return redirect('buyer-order-detail', order_id=order.id)


@login_required
@require_POST
def execute_order_payment_htmx(request, order_id):
    order = get_object_or_404(Order.objects.select_related('buyer', 'vendor'), id=order_id)
    if order.status != Order.Status.APPROVED:
        return render(request, 'partials/order_status_card.html', {'order': order, 'error_message': 'Only approved orders can be charged.'})

    if order.execute_payment(payment_method='JAZZCASH'):
        order.refresh_from_db()
        messages.success(request, f'Escrow locked for Order #{order.id}.')
    else:
        messages.error(request, f'Payment failed for Order #{order.id}.')
    return render(request, 'partials/order_status_card.html', {'order': order})


@login_required
@require_POST
def settle_escrow_htmx(request, order_id):
    order = get_object_or_404(Order.objects.select_related('buyer', 'vendor'), id=order_id)
    if order.status != Order.Status.PAID:
        return render(request, 'partials/order_status_card.html', {'order': order, 'error_message': 'Only paid orders can be settled.'})

    if order.complete_order():
        order.refresh_from_db()
        messages.success(request, f'Escrow released for Order #{order.id}.')
    else:
        messages.error(request, f'Settlement failed for Order #{order.id}.')
    return render(request, 'partials/order_status_card.html', {'order': order})


@login_required
@require_POST
def dispute_refund_htmx(request, order_id):
    order = get_object_or_404(Order.objects.select_related('buyer', 'vendor'), id=order_id)
    reason = request.POST.get('reason') or 'Quality dispute raised by buyer'
    if order.status != Order.Status.PAID:
        return render(request, 'partials/order_status_card.html', {'order': order, 'error_message': 'Only paid orders can be refunded.'})

    refund_reference = order.cancel_and_refund(reason=reason)
    order.refresh_from_db()
    if refund_reference:
        messages.warning(request, f'Order #{order.id} refunded.')
    else:
        messages.error(request, f'Refund failed for Order #{order.id}.')
    return render(request, 'partials/order_status_card.html', {'order': order})


@login_required
@require_GET
def vendor_dashboard(request):
    organization = _current_organization(request.user)
    orders = Order.objects.filter(vendor=organization).select_related('buyer', 'vendor').order_by('-id') if organization else Order.objects.none()
    return render(request, 'vendor/dashboard.html', {
        'organization': organization,
        'orders': orders,
        'pending_orders': [order for order in orders if order.status in {Order.Status.APPROVED, Order.Status.PAID}],
        'total_volume': sum((order.total_amount for order in orders), Decimal('0.00')),
        'paid_volume': sum((order.total_amount for order in orders if order.status == Order.Status.PAID), Decimal('0.00')),
        'completed_volume': sum((order.total_amount for order in orders if order.status == Order.Status.COMPLETED), Decimal('0.00')),
    })


@login_required
@require_GET
def vendor_wallet(request):
    organization = _current_organization(request.user)
    orders = Order.objects.filter(vendor=organization).select_related('buyer', 'vendor').order_by('-id') if organization else Order.objects.none()
    available_balance = sum((order.total_amount for order in orders if order.status == Order.Status.COMPLETED), Decimal('0.00'))
    escrow_balance = sum((order.total_amount for order in orders if order.status == Order.Status.PAID), Decimal('0.00'))
    return render(request, 'vendor/wallet.html', {
        'organization': organization,
        'orders': orders,
        'available_balance': available_balance,
        'escrow_balance': escrow_balance,
        'payout_ready': available_balance,
        'orders_count': orders.count(),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def vendor_payout(request):
    if request.method == 'POST':
        amount = request.POST.get('amount') or '0'
        messages.success(request, f'Payout request submitted for PKR {amount}.')
        return render(request, 'vendor/modals/payout_modal.html', {'success_message': 'Payout request submitted successfully.'})

    return render(request, 'vendor/modals/payout_modal.html', {})


@login_required
@require_GET
def vendor_wallet(request):
    organization = _get_current_organization(request.user)
    orders = Order.objects.filter(vendor=organization).select_related('buyer', 'vendor').order_by('-id') if organization else Order.objects.none()
    available_balance = sum((order.total_amount for order in orders if order.status == Order.Status.COMPLETED), Decimal('0.00'))
    escrow_balance = sum((order.total_amount for order in orders if order.status == Order.Status.PAID), Decimal('0.00'))
    context = {
        'organization': organization,
        'orders': orders,
        'available_balance': available_balance,
        'escrow_balance': escrow_balance,
        'payout_ready': available_balance,
        'orders_count': orders.count(),
    }
    return render(request, 'vendor/wallet.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def vendor_payout(request):
    if request.method == 'POST':
        amount = request.POST.get('amount') or '0'
        messages.success(request, f'Payout request submitted for PKR {amount}.')
        return render(request, 'vendor/modals/payout_modal.html', {
            'success_message': 'Payout request submitted successfully.',
        })

    return render(request, 'vendor/modals/payout_modal.html', {})
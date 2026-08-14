from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from apps.organizations.models import Organization, UserProfile
from apps.orders.models import Order
from .forms import RegistrationForm, LoginForm

def home_view(request):
    return render(request, 'home.html')

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
            tax_id = form.cleaned_data.get('tax_id', '')
            role = form.cleaned_data['role']

            # Check for existing username
            if User.objects.filter(username=username).exists():
                form.add_error('username', 'This username is already taken.')
                return render(request, 'auth/register.html', {'form': form})

            # 1. Create User
            user = User.objects.create_user(username=username, email=email, password=password)

            # 2. Create Organization & Profile
            org = Organization.objects.create(name=org_name, org_type=role, tax_id=tax_id)
            UserProfile.objects.create(user=user, organization=org, role=role)

            # 3. Log In Immediately
            login(request, user)

            # 4. Role-based direct navigation
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

    return render(request, 'auth/login.html', {'form': form})

def portal_logout(request):
    logout(request)
    return redirect('home')

@login_required(login_url='portal-login')
def portal_home(request):
    if hasattr(request.user, 'profile'):
        if request.user.profile.role == 'VENDOR':
            return redirect('vendor-dashboard')
        return redirect('buyer-catalog')
    return redirect('home')
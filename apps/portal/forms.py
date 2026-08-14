from django import forms

from apps.core.models import User
from apps.organizations.models import Organization


class EnterpriseRegistrationMixin:
    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean_company_name(self):
        company_name = self.cleaned_data['company_name'].strip()
        if Organization.objects.filter(name__iexact=company_name).exists():
            raise forms.ValidationError('An organization with this name already exists.')
        return company_name


class BuyerRegistrationForm(EnterpriseRegistrationMixin, forms.Form):
    company_name = forms.CharField(
        label="Enterprise / Organization Name",
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:outline-none text-sm'})
    )
    tax_id = forms.CharField(
        label="National Tax Number (NTN / Tax ID)",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:outline-none text-sm', 'placeholder': 'e.g. 1234567-8'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:outline-none text-sm'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:outline-none text-sm', 'placeholder': 'procurement@company.com'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:outline-none text-sm'})
    )

class VendorRegistrationForm(EnterpriseRegistrationMixin, forms.Form):
    company_name = forms.CharField(
        label="Supplier / Vendor Business Name",
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:outline-none text-sm'})
    )
    tax_id = forms.CharField(
        label="Sales Tax / NTN Registration",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:outline-none text-sm', 'placeholder': 'e.g. STRN-9876543-2'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:outline-none text-sm'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:outline-none text-sm', 'placeholder': 'sales@supplier.com'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:outline-none text-sm'})
    )
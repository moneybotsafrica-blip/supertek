from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(
        attrs={'class': 'form-control'}
    ))
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(
        attrs={'class': 'form-control'}
    ))
    last_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(
        attrs={'class': 'form-control'}
    ))
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email address already exists.")
        return email

class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information"""
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(
        attrs={'class': 'form-control'}
    ))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(
        attrs={'class': 'form-control'}
    ))
    email = forms.EmailField(required=True, widget=forms.EmailInput(
        attrs={'class': 'form-control'}
    ))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Phone number'}
    ))
    
    # Primary Address Fields
    address = forms.CharField(max_length=200, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Street address'}
    ))
    address_line2 = forms.CharField(max_length=200, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Apartment, suite, unit, etc. (optional)'}
    ))
    city = forms.CharField(max_length=100, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'City'}
    ))
    state_province = forms.CharField(max_length=100, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'State/Province/County'}
    ))
    postal_code = forms.CharField(max_length=20, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Postal code'}
    ))
    country = forms.CharField(max_length=100, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Country'}
    ))
    
    # Alternative Address (toggled with a checkbox)
    use_alternative_address = forms.BooleanField(required=False, initial=False, widget=forms.CheckboxInput(
        attrs={'class': 'form-check-input'}
    ))
    alt_address = forms.CharField(max_length=200, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Alternative street address'}
    ))
    alt_address_line2 = forms.CharField(max_length=200, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Apartment, suite, unit, etc. (optional)'}
    ))
    alt_city = forms.CharField(max_length=100, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'City'}
    ))
    alt_state_province = forms.CharField(max_length=100, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'State/Province/County'}
    ))
    alt_postal_code = forms.CharField(max_length=20, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Postal code'}
    ))
    alt_country = forms.CharField(max_length=100, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Country'}
    ))
    
    # Payment Method Fields
    default_payment_method = forms.ChoiceField(
        choices=[
            ('', '-- Select Payment Method --'),
            ('card', 'Credit/Debit Card'),
            ('mpesa', 'M-Pesa'),
            ('paypal', 'PayPal'),
            ('cash', 'Cash on Delivery')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # M-Pesa specific
    mpesa_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'M-Pesa registered phone number'}
    ))
    
    # Card details
    card_last_four = forms.CharField(max_length=4, required=False, widget=forms.TextInput(
        attrs={
            'class': 'form-control', 
            'placeholder': 'Last 4 digits of card',
            'pattern': '[0-9]{4}',
            'title': 'Please enter the last 4 digits of your card'
        }
    ))
    card_type = forms.ChoiceField(
        choices=[
            ('', '-- Select Card Type --'),
            ('visa', 'Visa'),
            ('mastercard', 'Mastercard'),
            ('amex', 'American Express'),
            ('other', 'Other')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    card_expiry = forms.CharField(max_length=7, required=False, widget=forms.TextInput(
        attrs={
            'class': 'form-control', 
            'placeholder': 'MM/YYYY',
            'pattern': '(0[1-9]|1[0-2])\/20[2-9][0-9]',
            'title': 'Please enter a valid expiry date in MM/YYYY format'
        }
    ))
    
    # Preferences
    receive_newsletter = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(
        attrs={'class': 'form-check-input'}
    ))
    preferred_currency = forms.ChoiceField(
        choices=[
            ('KES', 'Kenyan Shilling (KES)'),
            ('USD', 'US Dollar (USD)'),
            ('EUR', 'Euro (EUR)'),
            ('GBP', 'British Pound (GBP)')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        
        # If the user has a profile, populate form with profile data
        user = kwargs.get('instance')
        if user and hasattr(user, 'profile'):
            profile = user.profile
            self.initial.update({
                'phone': profile.phone,
                'address': profile.address,
                'address_line2': profile.address_line2,
                'city': profile.city,
                'state_province': profile.state_province,
                'postal_code': profile.postal_code,
                'country': profile.country,
                'use_alternative_address': bool(profile.alt_address),
                'alt_address': profile.alt_address,
                'alt_address_line2': profile.alt_address_line2,
                'alt_city': profile.alt_city,
                'alt_state_province': profile.alt_state_province,
                'alt_postal_code': profile.alt_postal_code,
                'alt_country': profile.alt_country,
                'default_payment_method': profile.default_payment_method,
                'mpesa_phone': profile.mpesa_phone,
                'card_last_four': profile.card_last_four,
                'card_type': profile.card_type,
                'card_expiry': profile.card_expiry,
                'receive_newsletter': profile.receive_newsletter,
                'preferred_currency': profile.preferred_currency
            })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = self.instance
        
        if email and User.objects.filter(email=email).exclude(pk=user.pk).exists():
            raise ValidationError("A user with this email address already exists.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        if commit:
            user.save()
            
            # Save profile data
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data.get('phone', '')
            profile.address = self.cleaned_data.get('address', '')
            profile.address_line2 = self.cleaned_data.get('address_line2', '')
            profile.city = self.cleaned_data.get('city', '')
            profile.state_province = self.cleaned_data.get('state_province', '')
            profile.postal_code = self.cleaned_data.get('postal_code', '')
            profile.country = self.cleaned_data.get('country', 'Kenya')
            
            # Only save alternative address if the checkbox is checked
            if self.cleaned_data.get('use_alternative_address'):
                profile.alt_address = self.cleaned_data.get('alt_address', '')
                profile.alt_address_line2 = self.cleaned_data.get('alt_address_line2', '')
                profile.alt_city = self.cleaned_data.get('alt_city', '')
                profile.alt_state_province = self.cleaned_data.get('alt_state_province', '')
                profile.alt_postal_code = self.cleaned_data.get('alt_postal_code', '')
                profile.alt_country = self.cleaned_data.get('alt_country', 'Kenya')
            else:
                profile.alt_address = None
                profile.alt_address_line2 = None
                profile.alt_city = None
                profile.alt_state_province = None
                profile.alt_postal_code = None
                profile.alt_country = None
            
            profile.default_payment_method = self.cleaned_data.get('default_payment_method', '')
            profile.mpesa_phone = self.cleaned_data.get('mpesa_phone', '')
            profile.card_last_four = self.cleaned_data.get('card_last_four', '')
            profile.card_type = self.cleaned_data.get('card_type', '')
            profile.card_expiry = self.cleaned_data.get('card_expiry', '')
            profile.receive_newsletter = self.cleaned_data.get('receive_newsletter', True)
            profile.preferred_currency = self.cleaned_data.get('preferred_currency', 'KES')
            profile.save()
            
        return user 
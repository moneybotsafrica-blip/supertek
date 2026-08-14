from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db.models import Sum

class SiteSettings(models.Model):
    """Global site settings including logo, contact info, etc."""
    site_name = models.CharField(max_length=200, default="Mustek East Africa")
    logo = models.ImageField(upload_to='site_settings', blank=True, null=True, help_text="Upload your site logo")
    favicon = models.ImageField(upload_to='site_settings', blank=True, null=True, help_text="Upload your site favicon")
    
    # Contact Information
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True, help_text="WhatsApp number with country code (e.g., 254700000000)")
    address = models.TextField(blank=True, null=True)
    
    # Social Media Links
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    
    # SEO Settings
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=500, blank=True, null=True)
    
    # Footer Settings
    footer_background_color = models.CharField(max_length=7, default="#333333", help_text="Hex color code (e.g., #333333)")
    footer_heading_color = models.CharField(max_length=7, default="#ffffff", help_text="Hex color code (e.g., #ffffff)")
    
    # Currency Settings
    default_currency = models.CharField(max_length=3, default="KES")
    
    # Business Hours
    business_hours = models.TextField(blank=True, null=True, help_text="e.g., Mon-Fri: 9AM-5PM, Sat: 10AM-2PM")
    
    # Header Messages
    header_message_1 = models.CharField(max_length=200, blank=True, null=True, default="Orders ship next day", help_text="First message in top bar")
    header_message_2 = models.CharField(max_length=200, blank=True, null=True, default="Logistics info updates within 1-2 working days", help_text="Second message in top bar")
    
    # Footer Messages
    footer_about_text = models.TextField(blank=True, null=True, default="Premium outdoor and camping equipment for all your adventures. Quality products for every outdoor experience.", help_text="About text in footer")
    
    # Promotional Popup
    enable_promo_popup = models.BooleanField(default=False, help_text="Enable promotional popup on site")
    promo_title = models.CharField(max_length=200, blank=True, null=True, default="EXCLUSIVE ONLINE DEAL", help_text="Promotional popup title")
    promo_message = models.TextField(blank=True, null=True, default="Buy any 2 camping items and get 15% OFF automatically at checkout!", help_text="Promotional popup message")
    
    PROMO_BACKGROUND_CHOICES = [
        ('#000000', 'Black'),
        ('#1a1a1a', 'Dark Gray'),
        ('#2c3e50', 'Dark Blue'),
        ('#34495e', 'Navy'),
        ('#8e44ad', 'Purple'),
        ('#2980b9', 'Blue'),
        ('#27ae60', 'Green'),
        ('#e67e22', 'Orange'),
        ('#c0392b', 'Red'),
        ('#ffffff', 'White'),
        ('#f8f9fa', 'Light Gray'),
    ]
    promo_background_color = models.CharField(
        max_length=7, 
        default="#000000", 
        choices=PROMO_BACKGROUND_CHOICES,
        help_text="Background color for promotional popup"
    )
    
    promo_button_text = models.CharField(max_length=50, blank=True, null=True, default="SHOP NOW", help_text="Button text for promotional popup")
    
    PROMO_BUTTON_CHOICES = [
        ('#dc3545', 'Red'),
        ('#c0392b', 'Dark Red'),
        ('#e74c3c', 'Light Red'),
        ('#007bff', 'Blue'),
        ('#17a2b8', 'Cyan'),
        ('#28a745', 'Green'),
        ('#ffc107', 'Yellow'),
        ('#fd7e14', 'Orange'),
        ('#6f42c1', 'Purple'),
        ('#343a40', 'Dark Gray'),
        ('#ffffff', 'White'),
    ]
    promo_button_color = models.CharField(
        max_length=7, 
        default="#dc3545", 
        choices=PROMO_BUTTON_CHOICES,
        help_text="Button color for promotional popup"
    )
    
    # Analytics
    google_analytics_id = models.CharField(max_length=50, blank=True, null=True, help_text="Google Analytics tracking ID")
    
    # Email Configuration
    email_host = models.CharField(max_length=100, blank=True, null=True, help_text="SMTP server hostname (e.g., smtp.gmail.com)")
    email_port = models.PositiveIntegerField(blank=True, null=True, help_text="SMTP server port (e.g., 587 for TLS, 465 for SSL)")
    email_use_tls = models.BooleanField(default=True, help_text="Use TLS for email sending")
    email_host_user = models.CharField(max_length=100, blank=True, null=True, help_text="SMTP username (usually email address)")
    email_host_password = models.CharField(max_length=100, blank=True, null=True, help_text="SMTP password")
    default_from_email = models.EmailField(blank=True, null=True, help_text="Default sender email address")
    email_backend = models.CharField(max_length=100, default='django.core.mail.backends.smtp.EmailBackend', 
                                    help_text="Email backend to use")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Company Profile"
        verbose_name_plural = "Company Profile"
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError("Only one SiteSettings instance is allowed. Please edit the existing instance.")
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get the single SiteSettings instance, create default if doesn't exist"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'site_name': 'Mustek East Africa',
                'contact_email': 'info@mustekeastafrica.com',
                'contact_phone': '+254 700 000 000',
                'whatsapp_number': '254700000000',
                'address': 'Nairobi, Kenya',
                'footer_background_color': '#333333',
                'footer_heading_color': '#ffffff',
                'default_currency': 'KES',
            }
        )
        return settings

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories', blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ('name',)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('store:category_detail', args=[self.slug])

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # For sales/discounts
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    is_available = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    featured = models.BooleanField(default=False)
    product_line = models.CharField(max_length=100, blank=True)  # e.g., "Vitamin C", "Retinol"
    skin_concern = models.CharField(max_length=100, blank=True)  # e.g., "Acne Skin", "Dry Skin"
    
    class Meta:
        ordering = ('-created_at',)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.slug])
    
    def get_active_discount(self):
        """Get the best active discount for this product"""
        from django.utils import timezone
        now = timezone.now()
        
        # Get all valid discounts that apply to this product
        valid_discounts = []
        for discount in self.discounts.filter(is_active=True):
            if discount.is_valid() and discount.applies_to_product(self):
                valid_discounts.append(discount)
        
        # Also check category discounts
        for discount in self.category.discounts.filter(is_active=True):
            if discount.is_valid() and discount.applies_to_product(self):
                valid_discounts.append(discount)
        
        # Return the discount with the highest value
        if valid_discounts:
            return max(valid_discounts, key=lambda d: d.calculate_discount(self.price))
        return None
    
    def get_active_flash_sale(self):
        """Get the active flash sale for this product"""
        from django.utils import timezone
        now = timezone.now()
        
        for flash_sale in self.flash_sales.filter(is_active=True):
            if flash_sale.is_active_now() and not flash_sale.is_sold_out():
                return flash_sale
        return None
    
    def get_active_offers(self):
        """Get all active offers for this product"""
        from django.utils import timezone
        now = timezone.now()
        
        valid_offers = []
        for offer in self.offers.filter(is_active=True):
            if offer.is_valid():
                valid_offers.append(offer)
        
        # Also check category offers
        for offer in self.category.offers.filter(is_active=True):
            if offer.is_valid():
                valid_offers.append(offer)
        
        return valid_offers
    
    def get_discounted_price(self):
        """Calculate the final price after applying best discount"""
        # Start with original price
        final_price = self.price
        
        # Check for flash sales first (highest priority)
        flash_sale = self.get_active_flash_sale()
        if flash_sale:
            final_price = flash_sale.get_discounted_price(final_price)
        
        # Then check for regular discounts
        discount = self.get_active_discount()
        if discount:
            discount_amount = discount.calculate_discount(final_price)
            final_price = final_price - discount_amount
        
        # Ensure price doesn't go below zero
        return max(final_price, 0)
    
    def get_discount_percentage(self):
        """Get the discount percentage for display"""
        if self.original_price and self.original_price > self.price:
            discount = ((self.original_price - self.price) / self.original_price) * 100
            return round(discount, 1)
        
        # Calculate from active discounts
        discounted_price = self.get_discounted_price()
        if discounted_price < self.price:
            discount = ((self.price - discounted_price) / self.price) * 100
            return round(discount, 1)
        
        return 0
    
    def has_discount(self):
        """Check if product has any active discount"""
        return self.get_discounted_price() < self.price or (self.original_price and self.original_price > self.price)

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products')
    is_main = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Image for {self.product.name}"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart {self.id}"
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    @property
    def total_price(self):
        return self.product.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending_payment', 'Pending Payment'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash_on_delivery', 'Cash on Delivery'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='mpesa')
    payment_status = models.CharField(max_length=20, default='pending',
                                     choices=(
                                         ('pending', 'Pending'),
                                         ('processing', 'Processing'),
                                         ('completed', 'Completed'),
                                         ('failed', 'Failed'),
                                         ('refunded', 'Refunded'),
                                     ))
    delivery_instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.id}"
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Save price at time of purchase
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    @property
    def total_price(self):
        return self.price * self.quantity

class MpesaConfiguration(models.Model):
    """M-Pesa API Configuration"""
    consumer_key = models.CharField(max_length=100)
    consumer_secret = models.CharField(max_length=100)
    passkey = models.CharField(max_length=100, blank=True, null=True)
    shortcode = models.CharField(max_length=10, help_text="Business Short Code")
    environment = models.CharField(max_length=10, choices=[('sandbox', 'Sandbox'), ('production', 'Production')], default='sandbox')
    callback_url = models.URLField(blank=True, null=True, help_text="Callback URL for M-Pesa responses")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "M-Pesa Configuration"
        verbose_name_plural = "M-Pesa Configurations"
    
    def __str__(self):
        return f"M-Pesa Config ({self.environment})"

class MpesaTransaction(models.Model):
    """M-Pesa Transaction Records"""
    TRANSACTION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='mpesa_transactions')
    merchant_request_id = models.CharField(max_length=100, unique=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    response_code = models.CharField(max_length=10, blank=True, null=True)
    response_description = models.TextField(blank=True, null=True)
    customer_message = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=20)
    transaction_date = models.DateTimeField(blank=True, null=True)
    receipt_number = models.CharField(max_length=100, blank=True, null=True, help_text="M-Pesa Receipt Number")
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "M-Pesa Transaction"
        verbose_name_plural = "M-Pesa Transactions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"M-Pesa Transaction {self.merchant_request_id}"

class Banner(models.Model):
    """Banner and promotional images for the website"""
    BANNER_TYPE_CHOICES = (
        ('hero', 'Hero Slider'),
        ('advert', 'Advertisement Bar'),
        ('promo', 'Promotional Banner'),
        ('category', 'Category Banner'),
        ('bestseller', 'Bestseller Banner'),
    )
    
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='banners')
    banner_type = models.CharField(max_length=20, choices=BANNER_TYPE_CHOICES, default='hero')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True, related_name='banners', help_text="Optional: Link to specific category for category-specific banners")
    link_url = models.URLField(blank=True, null=True, help_text="URL to link to when clicked")
    alt_text = models.CharField(max_length=200, blank=True, help_text="Alt text for accessibility")
    description = models.TextField(blank=True, help_text="Description text for banner content (especially for bestseller banners)")
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0, help_text="Lower numbers display first")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Banner"
        verbose_name_plural = "Banners"
        ordering = ['display_order', '-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_banner_type_display()})"

class Advertisement(models.Model):
    """Advertisement images for the advertisement bar"""
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='advertisements')
    link_url = models.URLField(blank=True, null=True, help_text="URL to link to when clicked")
    alt_text = models.CharField(max_length=200, blank=True, help_text="Alt text for accessibility")
    description = models.TextField(blank=True, help_text="Description text for advertisement content")
    background_color = models.CharField(max_length=7, default="#ff0000", help_text="Background color for advertisement panel (hex code)")
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0, help_text="Lower numbers display first")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Advertisement"
        verbose_name_plural = "Advertisements"
        ordering = ['display_order', '-created_at']
    
    def __str__(self):
        return self.title

class Video(models.Model):
    """Video content for the website"""
    title = models.CharField(max_length=200)
    video_file = models.FileField(upload_to='videos', blank=True, null=True, help_text="Upload video file")
    video_url = models.URLField(blank=True, null=True, help_text="Or provide video URL (YouTube, Vimeo, etc.)")
    thumbnail = models.ImageField(upload_to='video_thumbnails', blank=True, null=True, help_text="Video thumbnail image")
    description = models.TextField(blank=True)
    section = models.CharField(max_length=50, choices=[
        ('hero', 'Hero Section'),
        ('product', 'Product Showcase'),
        ('about', 'About Us'),
        ('other', 'Other'),
    ], default='other')
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0, help_text="Lower numbers display first")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        ordering = ['display_order', '-created_at']
    
    def __str__(self):
        return self.title

class Newsletter(models.Model):
    """Newsletter images and content"""
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='newsletter')
    description = models.TextField(blank=True)
    link_url = models.URLField(blank=True, null=True, help_text="URL to link to when clicked")
    alt_text = models.CharField(max_length=200, blank=True, help_text="Alt text for accessibility")
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0, help_text="Lower numbers display first")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Newsletter"
        verbose_name_plural = "Newsletters"
        ordering = ['display_order', '-created_at']
    
    def __str__(self):
        return self.title

class FeaturedProduct(models.Model):
    """Featured product images and settings"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='featured_settings')
    image = models.ImageField(upload_to='featured_products', blank=True, null=True, help_text="Custom featured image (optional)")
    title = models.CharField(max_length=200, blank=True, help_text="Custom title for featured display")
    description = models.TextField(blank=True, help_text="Custom description for featured display")
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0, help_text="Lower numbers display first")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Featured Product"
        verbose_name_plural = "Featured Products"
        ordering = ['display_order', '-created_at']
    
    def __str__(self):
        return f"{self.product.name} (Featured)"

class Brand(models.Model):
    """Brand cards for the shop page"""
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='brands')
    description = models.TextField(blank=True)
    link_url = models.URLField(blank=True, null=True, help_text="URL to link to when clicked")
    alt_text = models.CharField(max_length=200, blank=True, help_text="Alt text for accessibility")
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0, help_text="Lower numbers display first")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Brands"
        ordering = ['display_order', '-created_at']
    
    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # Contact information
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Primary address (shipping)
    address = models.CharField(max_length=200, blank=True, null=True)
    address_line2 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default="Kenya", blank=True, null=True)
    
    # Optional alternative shipping address
    alt_address = models.CharField("Alternative Address", max_length=200, blank=True, null=True)
    alt_address_line2 = models.CharField("Alternative Address Line 2", max_length=200, blank=True, null=True)
    alt_city = models.CharField("Alternative City", max_length=100, blank=True, null=True)
    alt_state_province = models.CharField("Alternative State/Province", max_length=100, blank=True, null=True)
    alt_postal_code = models.CharField("Alternative Postal Code", max_length=20, blank=True, null=True)
    alt_country = models.CharField("Alternative Country", max_length=100, default="Kenya", blank=True, null=True)
    
    # Payment information
    default_payment_method = models.CharField(max_length=100, blank=True, null=True, 
                                             choices=[
                                                 ('card', 'Credit/Debit Card'),
                                                 ('mpesa', 'M-Pesa'),
                                                 ('paypal', 'PayPal'),
                                                 ('cash', 'Cash on Delivery')
                                             ])
    
    # M-Pesa specific details
    mpesa_phone = models.CharField("M-Pesa Phone Number", max_length=20, blank=True, null=True, 
                                   help_text="Phone number registered with M-Pesa")
    
    # Card details (last 4 digits only for reference)
    card_last_four = models.CharField(max_length=4, blank=True, null=True)
    card_type = models.CharField(max_length=50, blank=True, null=True,
                                choices=[
                                    ('visa', 'Visa'),
                                    ('mastercard', 'Mastercard'),
                                    ('amex', 'American Express'),
                                    ('other', 'Other')
                                ])
    card_expiry = models.CharField(max_length=7, blank=True, null=True, 
                                  help_text="MM/YYYY format")
    
    # Preferences
    receive_newsletter = models.BooleanField(default=True)
    preferred_currency = models.CharField(max_length=3, default="KES", 
                                         choices=[
                                             ('KES', 'Kenyan Shilling'),
                                             ('USD', 'US Dollar'),
                                             ('EUR', 'Euro'),
                                             ('GBP', 'British Pound')
                                         ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile for {self.user.username}"
    
    def get_full_address(self):
        """Return formatted full address"""
        parts = [self.address]
        if self.address_line2:
            parts.append(self.address_line2)
        if self.city:
            parts.append(self.city)
        if self.state_province:
            parts.append(self.state_province)
        if self.postal_code:
            parts.append(self.postal_code)
        if self.country:
            parts.append(self.country)
        return ", ".join(filter(None, parts))
    
    def has_complete_shipping_info(self):
        """Check if user has completed minimum shipping information"""
        return all([self.address, self.city, self.phone])
    
    def has_complete_payment_info(self):
        """Check if user has a valid payment method set up"""
        if not self.default_payment_method:
            return False
        if self.default_payment_method == 'mpesa' and not self.mpesa_phone:
            return False
        if self.default_payment_method == 'card' and not self.card_last_four:
            return False
        return True

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update user profile when user is created/updated"""
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if not hasattr(instance, 'profile'):
            UserProfile.objects.create(user=instance)

# Discount and Sales Management Models

class Discount(models.Model):
    """General discount that can be applied to products or categories"""
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage (e.g., 15 for 15%) or fixed amount")
    
    # Applicability
    applies_to = models.CharField(max_length=20, choices=[
        ('all_products', 'All Products'),
        ('specific_products', 'Specific Products'),
        ('categories', 'Categories'),
    ], default='all_products')
    
    # For specific products/categories
    products = models.ManyToManyField(Product, blank=True, related_name='discounts')
    categories = models.ManyToManyField(Category, blank=True, related_name='discounts')
    
    # Date constraints
    start_date = models.DateTimeField(help_text="When this discount becomes active")
    end_date = models.DateTimeField(help_text="When this discount expires")
    
    # Usage constraints
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Minimum purchase amount to qualify")
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum discount amount")
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Total number of times this discount can be used")
    usage_count = models.PositiveIntegerField(default=0, help_text="Number of times this discount has been used")
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ('-created_at',)
    
    def __str__(self):
        return f"{self.name} ({self.get_discount_value_display()})"
    
    def get_discount_value_display(self):
        if self.discount_type == 'percentage':
            return f"{self.discount_value}%"
        else:
            return f"KES {self.discount_value}"
    
    def is_valid(self):
        """Check if discount is currently valid"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.start_date > now:
            return False
        
        if self.end_date < now:
            return False
        
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False
        
        return True
    
    def calculate_discount(self, original_price):
        """Calculate discount amount for a given price"""
        if not self.is_valid():
            return 0
        
        if self.discount_type == 'percentage':
            discount_amount = original_price * (self.discount_value / 100)
        else:
            discount_amount = self.discount_value
        
        # Apply maximum discount limit if set
        if self.max_discount_amount and discount_amount > self.max_discount_amount:
            discount_amount = self.max_discount_amount
        
        return discount_amount
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.save()
    
    def applies_to_product(self, product):
        """Check if discount applies to a specific product"""
        if self.applies_to == 'all_products':
            return True
        elif self.applies_to == 'specific_products':
            return self.products.filter(id=product.id).exists()
        elif self.applies_to == 'categories':
            return self.categories.filter(id=product.category.id).exists()
        return False

class FlashSale(models.Model):
    """Limited-time flash sales with urgent discounts"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Products included in flash sale
    products = models.ManyToManyField(Product, related_name='flash_sales')
    
    # Discount details
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Discount percentage (e.g., 30 for 30% off)")
    
    # Timing
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    # Stock limits
    max_quantity_per_customer = models.PositiveIntegerField(default=1, help_text="Max quantity each customer can purchase")
    total_stock_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Total stock available for this sale")
    sold_count = models.PositiveIntegerField(default=0, help_text="Number of items sold")
    
    # Popup styling
    background_color = models.CharField(max_length=7, default="#ff0000", help_text="Background color for flash sale popup (hex code)")
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('-created_at',)
    
    def __str__(self):
        return f"{self.name} ({self.discount_percentage}% off)"
    
    def is_active_now(self):
        """Check if flash sale is currently active"""
        from django.utils import timezone
        now = timezone.now()
        return (self.is_active and 
                self.start_time is not None and 
                self.end_time is not None and 
                self.start_time <= now <= self.end_time)
    
    def is_sold_out(self):
        """Check if flash sale is sold out"""
        if self.total_stock_limit:
            return self.sold_count >= self.total_stock_limit
        return False
    
    def get_discounted_price(self, original_price):
        """Calculate discounted price"""
        if not self.is_active_now() or self.is_sold_out():
            return original_price
        
        discount_amount = original_price * (self.discount_percentage / 100)
        return original_price - discount_amount

class Offer(models.Model):
    """Special offers and promotions"""
    OFFER_TYPE_CHOICES = [
        ('buy_x_get_y', 'Buy X Get Y Free'),
        ('bundle', 'Bundle Deal'),
        ('free_shipping', 'Free Shipping'),
        ('gift_with_purchase', 'Gift with Purchase'),
        ('tiered_discount', 'Tiered Discount'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    offer_type = models.CharField(max_length=30, choices=OFFER_TYPE_CHOICES)
    
    # Products involved
    products = models.ManyToManyField(Product, blank=True, related_name='offers')
    categories = models.ManyToManyField(Category, blank=True, related_name='offers')
    
    # Offer parameters
    buy_quantity = models.PositiveIntegerField(null=True, blank=True, help_text="Quantity to buy (for Buy X Get Y)")
    get_quantity = models.PositiveIntegerField(null=True, blank=True, help_text="Quantity to get free (for Buy X Get Y)")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Discount percentage for bundle/tiered deals")
    
    # Free gift product (for Gift with Purchase)
    gift_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='gift_offers')
    
    # Minimum purchase amount
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Timing
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('-created_at',)
    
    def __str__(self):
        return f"{self.name} ({self.get_offer_type_display()})"
    
    def is_valid(self):
        """Check if offer is currently valid"""
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

# Service Booking and Technician Management Models

class Service(models.Model):
    """Services offered for repair/installation"""
    SERVICE_TYPES = [
        ('repair', 'Repair'),
        ('installation', 'Installation'),
        ('maintenance', 'Maintenance'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=3750.00)  # Base service fee
    callout_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Additional callout fee for service visits")
    image = models.ImageField(upload_to='services', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('name',)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('store:service_detail', args=[self.slug])
    
    def get_total_price(self):
        """Calculate total price including callout fee"""
        return self.base_price + self.callout_fee

class ServiceHeroSlide(models.Model):
    """Hero slide images for the services page"""
    title = models.CharField(max_length=200, help_text="Slide title/headline")
    subtitle = models.CharField(max_length=300, blank=True, help_text="Subtitle or description text")
    description = models.TextField(blank=True, help_text="Detailed description based on the image content")
    image = models.ImageField(upload_to='service_hero_slides', help_text="Hero slide image")
    link_url = models.URLField(blank=True, null=True, help_text="Optional URL to link to when clicked")
    alt_text = models.CharField(max_length=200, blank=True, help_text="Alt text for accessibility")
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0, help_text="Lower numbers display first")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Service Hero Slide"
        verbose_name_plural = "Service Hero Slides"
        ordering = ['display_order', '-created_at']
    
    def __str__(self):
        return self.title

class Technician(models.Model):
    """Technician information and skills"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='technician_profile')
    phone = models.CharField(max_length=20)
    skills = models.ManyToManyField(Service, related_name='technicians')
    is_available = models.BooleanField(default=True)
    has_admin_access = models.BooleanField(default=False, help_text="Grant this technician access to the Django admin panel")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_jobs = models.PositiveIntegerField(default=0)
    total_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('-rating', '-total_jobs')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Technician"
    
    def get_assigned_bookings(self):
        return self.bookings.filter(status='assigned').order_by('scheduled_date')
    
    def get_total_hours_worked(self):
        return self.clock_in_logs.aggregate(total=Sum('hours_worked'))['total'] or 0

class ClockInLog(models.Model):
    """Track technician clock-in/out hours"""
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE, related_name='clock_in_logs')
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='clock_in_logs', null=True, blank=True)
    clock_in_time = models.DateTimeField()
    clock_out_time = models.DateTimeField(null=True, blank=True)
    hours_worked = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    notes = models.TextField(blank=True)
    date = models.DateField(auto_now_add=True)
    
    class Meta:
        ordering = ('-date', '-clock_in_time')
    
    def __str__(self):
        return f"{self.technician.user.get_full_name} - {self.date}"
    
    def calculate_hours(self):
        if self.clock_out_time:
            duration = self.clock_out_time - self.clock_in_time
            self.hours_worked = duration.total_seconds() / 3600
            self.save()

class SiteImage(models.Model):
    """Site images for bookings and jobs"""
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='site_images')
    image = models.ImageField(upload_to='site_images/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('-uploaded_at',)
    
    def __str__(self):
        return f"Image for Booking #{self.booking.id}"

class Vehicle(models.Model):
    """Vehicle for technician fleet management"""
    registration_number = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    assigned_technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('registration_number',)
    
    def __str__(self):
        return f"{self.registration_number} - {self.make} {self.model}"
    
    def get_current_mileage(self):
        latest_log = self.logs.order_by('-date').first()
        return latest_log.mileage if latest_log else 0

class VehicleLog(models.Model):
    """Daily mileage tracking for vehicles"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField()
    starting_mileage = models.PositiveIntegerField()
    ending_mileage = models.PositiveIntegerField()
    distance_traveled = models.PositiveIntegerField()
    fuel_consumed = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True)
    logged_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('-date',)
        unique_together = ('vehicle', 'date')
    
    def __str__(self):
        return f"{self.vehicle.registration_number} - {self.date}"
    
    def save(self, *args, **kwargs):
        self.distance_traveled = self.ending_mileage - self.starting_mileage
        super().save(*args, **kwargs)

class Booking(models.Model):
    """Service booking model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
    ]
    
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    
    scheduled_date = models.DateTimeField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    
    # Payment fields
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ('-created_at',)
    
    def __str__(self):
        return f"Booking #{self.id} - {self.service.name}"
    
    def get_total_cost(self):
        """Calculate total cost including base service fee, callout fee and VAT"""
        from decimal import Decimal
        vat_rate = Decimal('0.16')  # 16% VAT in Kenya
        base_fee = self.service.base_price
        callout_fee = self.service.callout_fee
        subtotal = base_fee + callout_fee
        vat_amount = subtotal * vat_rate
        return subtotal + vat_amount

class Quotation(models.Model):
    """Service quotation linked to booking and spare parts"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='quotations')
    quotation_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    notes = models.TextField(blank=True)
    valid_until = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ('-created_at',)
    
    def __str__(self):
        return f"Quotation {self.quotation_number}"
    
    def save(self, *args, **kwargs):
        if not self.quotation_number:
            self.quotation_number = f"QT-{self.booking.id}-{self.created_at.strftime('%Y%m%d')}"
        
        # Calculate VAT (16% in Kenya)
        vat_rate = 0.16
        subtotal = self.labor_cost + self.parts_cost
        self.vat_amount = subtotal * vat_rate
        self.total_amount = subtotal + self.vat_amount
        
        super().save(*args, **kwargs)

class QuotationItem(models.Model):
    """Individual items in a quotation"""
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.description} - {self.quotation.quotation_number}"

class Payment(models.Model):
    """Payment for services"""
    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    quotation = models.ForeignKey(Quotation, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('-created_at',)
    
    def __str__(self):
        return f"Payment {self.id} - {self.amount}"

class Receipt(models.Model):
    """Receipt for payments"""
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=50, unique=True)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='issued_receipts')
    issued_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Receipt {self.receipt_number}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"RCPT-{self.payment.id}-{self.issued_at.strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)

@receiver(post_save, sender=Technician)
def sync_technician_admin_access(sender, instance, created, **kwargs):
    """Sync technician admin access with user's staff status"""
    # Only update if the status has changed to avoid recursion
    if instance.user.is_staff != instance.has_admin_access:
        instance.user.is_staff = instance.has_admin_access
        instance.user.is_superuser = False  # Technicians are staff but not superusers
        instance.user.save(update_fields=['is_staff', 'is_superuser'])

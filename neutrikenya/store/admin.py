from django.contrib import admin
from django import forms
from .models import (
    Category, Product, ProductImage, Cart, CartItem, Order, OrderItem, 
    MpesaConfiguration, MpesaTransaction, Banner, Advertisement, Video, 
    Newsletter, FeaturedProduct, Brand, Service, ServiceHeroSlide, Technician, Vehicle, 
    VehicleLog, Booking, Quotation, QuotationItem, Payment, Receipt,
    Discount, FlashSale, Offer, SiteSettings, ClockInLog, SiteImage
)

# Admin Site Branding
admin.site.site_header = "Mustek East Africa Admin"
admin.site.site_title = "Mustek East Africa"
admin.site.index_title = "Welcome to Mustek East Africa Administration"

class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin interface for company profile - singleton pattern"""
    def has_add_permission(self, request):
        # Prevent adding new instances if one already exists
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the settings instance
        return False
    
    list_display = ('site_name', 'contact_email', 'contact_phone', 'email_host', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'logo_preview', 'favicon_preview')
    fieldsets = (
        ('Company Profile', {
            'fields': ('site_name', 'logo', 'logo_preview', 'favicon', 'favicon_preview'),
            'description': 'Manage your company branding - name and visual identity'
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'whatsapp_number', 'address', 'business_hours'),
            'description': 'How customers can reach your business'
        }),
        ('Social Media Links', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url'),
            'description': 'Connect with customers on social platforms'
        }),
        ('Website Messages', {
            'fields': ('header_message_1', 'header_message_2', 'footer_about_text'),
            'description': 'Custom messages displayed throughout the website'
        }),
        ('Marketing & Promotions', {
            'fields': ('enable_promo_popup', 'promo_title', 'promo_message', 'promo_background_color', 'promo_button_text', 'promo_button_color'),
            'description': 'Configure promotional popup for marketing campaigns'
        }),
        ('SEO & Analytics', {
            'fields': ('meta_description', 'meta_keywords', 'google_analytics_id'),
            'description': 'Search engine optimization and tracking'
        }),
        ('Email Configuration', {
            'fields': ('email_host', 'email_port', 'email_use_tls', 'email_host_user', 'email_host_password', 'default_from_email', 'email_backend'),
            'description': 'Configure email server settings for sending notifications and automated emails'
        }),
        ('Appearance Settings', {
            'fields': ('footer_background_color', 'footer_heading_color', 'default_currency'),
            'description': 'Customize the look and feel of your website'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Technical timestamps - not editable'
        }),
    )
    
    def logo_preview(self, obj):
        if obj.logo:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="width: 200px; height: auto; border: 1px solid #ddd; padding: 5px; background: #fff;" />', obj.logo.url)
        return '<span style="color: #999; font-style: italic;">No logo uploaded</span>'
    logo_preview.short_description = 'Logo Preview'
    
    def favicon_preview(self, obj):
        if obj.favicon:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="width: 32px; height: 32px; border: 1px solid #ddd; padding: 2px; background: #fff;" />', obj.favicon.url)
        return '<span style="color: #999; font-style: italic;">No favicon uploaded</span>'
    favicon_preview.short_description = 'Favicon Preview'

# Register Company Profile first (singleton)
admin.site.register(SiteSettings, SiteSettingsAdmin)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'discounted_price_display', 'category', 'product_line', 'is_available', 'stock', 'created_at')
    list_filter = ('is_available', 'category', 'product_line', 'skin_concern')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    readonly_fields = ('discounted_price_display', 'active_discounts_display')
    
    def discounted_price_display(self, obj):
        discounted_price = obj.get_discounted_price()
        if discounted_price < obj.price:
            return f"KES {discounted_price} (was KES {obj.price})"
        return f"KES {obj.price}"
    discounted_price_display.short_description = 'Current Price'
    
    def active_discounts_display(self, obj):
        discounts = []
        
        # Check flash sales
        flash_sale = obj.get_active_flash_sale()
        if flash_sale:
            discounts.append(f"Flash Sale: {flash_sale.discount_percentage}%")
        
        # Check regular discounts
        discount = obj.get_active_discount()
        if discount:
            discounts.append(f"Discount: {discount.get_discount_value_display()}")
        
        # Check offers
        offers = obj.get_active_offers()
        for offer in offers:
            discounts.append(f"Offer: {offer.get_offer_type_display()}")
        
        return ", ".join(discounts) if discounts else "No active discounts"
    active_discounts_display.short_description = 'Active Discounts'

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'image_preview', 'product_count', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('image_preview', 'product_count')
    search_fields = ('name', 'description')
    list_filter = ('parent',)
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'slug', 'parent', 'description')
        }),
        ('Category Image', {
            'fields': ('image', 'image_preview')
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="width: 100px; height: 100px; object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image Preview'
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'
    
    def is_active(self, obj):
        return obj.products.filter(is_available=True).exists()
    is_active.boolean = True
    is_active.short_description = 'Has Active Products'

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ('product', 'quantity', 'total_price')
    readonly_fields = ('total_price',)
    can_delete = True

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'total_price')
    list_filter = ('cart', 'product')
    search_fields = ('product__name', 'cart__user__username')
    list_editable = ('quantity',)
    readonly_fields = ('total_price',)

class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_id', 'item_count', 'total_price', 'created_at')
    inlines = [CartItemInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'first_name', 'last_name', 'email', 'status', 'payment_method', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_method', 'payment_status', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    inlines = [OrderItemInline]

class MpesaTransactionInline(admin.TabularInline):
    model = MpesaTransaction
    extra = 0
    readonly_fields = ('merchant_request_id', 'checkout_request_id', 'response_code', 'response_description', 'customer_message', 'amount', 'phone_number', 'transaction_date', 'receipt_number', 'status')

class MpesaConfigurationAdmin(admin.ModelAdmin):
    list_display = ('shortcode', 'environment', 'is_active', 'created_at', 'updated_at')
    list_filter = ('environment', 'is_active')
    search_fields = ('shortcode', 'consumer_key')
    fieldsets = (
        ('API Credentials', {
            'fields': ('consumer_key', 'consumer_secret', 'passkey')
        }),
        ('Business Details', {
            'fields': ('shortcode', 'environment', 'callback_url')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )

class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ('merchant_request_id', 'order', 'amount', 'phone_number', 'receipt_number', 'status', 'transaction_date', 'created_at')
    list_filter = ('status', 'transaction_date', 'created_at')
    search_fields = ('merchant_request_id', 'receipt_number', 'phone_number', 'order__id')
    readonly_fields = ('merchant_request_id', 'checkout_request_id', 'response_code', 'response_description', 'customer_message', 'amount', 'phone_number', 'transaction_date', 'receipt_number', 'status', 'created_at', 'updated_at')
    fieldsets = (
        ('Transaction Details', {
            'fields': ('order', 'merchant_request_id', 'checkout_request_id', 'amount', 'phone_number')
        }),
        ('M-Pesa Response', {
            'fields': ('response_code', 'response_description', 'customer_message', 'receipt_number', 'transaction_date')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'banner_type', 'category', 'image_preview', 'is_active', 'display_order', 'created_at')
    list_filter = ('banner_type', 'category', 'is_active', 'created_at')
    search_fields = ('title', 'alt_text', 'description')
    list_editable = ('is_active', 'display_order')
    readonly_fields = ('image_preview',)
    fieldsets = (
        ('Banner Details', {
            'fields': ('title', 'banner_type', 'category', 'image', 'image_preview')
        }),
        ('Content', {
            'fields': ('description',),
            'description': 'Add description text for bestseller banners and other promotional content'
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_order', 'link_url', 'alt_text')
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="width: 200px; height: auto;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'

class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_main', 'image_preview')
    list_filter = ('is_main',)
    search_fields = ('product__name',)
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="width: 100px; height: 100px; object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image'

# Service Booking and Technician Management Admin Classes

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type', 'base_price', 'callout_fee', 'is_active', 'created_at')
    list_filter = ('service_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}

class ServiceHeroSlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'image_preview', 'is_active', 'display_order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'subtitle', 'description', 'alt_text')
    list_editable = ('is_active', 'display_order')
    readonly_fields = ('image_preview',)
    fieldsets = (
        ('Slide Content', {
            'fields': ('title', 'subtitle', 'description', 'image', 'image_preview')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_order', 'link_url', 'alt_text')
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="width: 300px; height: auto;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image Preview'

class TechnicianAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'phone', 'is_available', 'has_admin_access', 'rating', 'total_jobs', 'skills_display', 'created_at')
    list_filter = ('is_available', 'has_admin_access', 'skills', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'phone')
    filter_horizontal = ('skills',)
    list_editable = ('is_available', 'has_admin_access')
    fieldsets = (
        ('Technician Information', {
            'fields': ('user', 'phone', 'is_available', 'has_admin_access')
        }),
        ('Skills & Specializations', {
            'fields': ('skills',),
            'description': 'Select the services this technician is qualified to perform. These skills will be used for automatic assignment when customers book services.'
        }),
        ('Performance Metrics', {
            'fields': ('rating', 'total_jobs', 'total_hours'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('rating', 'total_jobs', 'total_hours')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Technicians can only see their own profile
        if hasattr(request.user, 'technician_profile'):
            return qs.filter(user=request.user)
        return qs.none()
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'
    
    def skills_display(self, obj):
        return ", ".join([skill.name for skill in obj.skills.all()])
    skills_display.short_description = 'Skills'

class VehicleAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'make', 'model', 'year', 'assigned_technician', 'is_active')
    list_filter = ('is_active', 'make')
    search_fields = ('registration_number', 'make', 'model')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Technicians can only see their assigned vehicles
        if hasattr(request.user, 'technician_profile'):
            return qs.filter(assigned_technician=request.user.technician_profile)
        return qs

class VehicleLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'date', 'starting_mileage', 'ending_mileage', 'distance_traveled', 'logged_by')
    list_filter = ('date', 'vehicle')
    search_fields = ('vehicle__registration_number', 'notes')
    readonly_fields = ('distance_traveled',)

class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'service', 'customer', 'technician', 'scheduled_date', 'status', 'created_at')
    list_filter = ('status', 'service', 'scheduled_date', 'created_at')
    search_fields = ('customer__username', 'customer__email', 'address', 'city')
    list_editable = ('status',)
    date_hierarchy = 'scheduled_date'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Technicians can only see their own bookings
        if hasattr(request.user, 'technician_profile'):
            return qs.filter(technician=request.user.technician_profile)
        return qs
    
    def has_add_permission(self, request):
        # Only superusers can add bookings through admin
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        # Technicians can change their own bookings
        if hasattr(request.user, 'technician_profile'):
            if obj is None:
                return True
            return obj.technician == request.user.technician_profile
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete bookings
        return request.user.is_superuser

class QuotationAdmin(admin.ModelAdmin):
    list_display = ('quotation_number', 'booking', 'status', 'labor_cost', 'parts_cost', 'total_amount', 'valid_until')
    list_filter = ('status', 'valid_until', 'created_at')
    search_fields = ('quotation_number', 'booking__customer__username')
    list_editable = ('status',)
    readonly_fields = ('quotation_number', 'vat_amount', 'total_amount')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Technicians can only see their own quotations
        if hasattr(request.user, 'technician_profile'):
            return qs.filter(booking__technician=request.user.technician_profile)
        return qs

class QuotationItemAdmin(admin.ModelAdmin):
    list_display = ('quotation', 'product', 'description', 'quantity', 'unit_price', 'total_price')
    list_filter = ('quotation',)
    search_fields = ('description', 'product__name')
    readonly_fields = ('total_price',)

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'payment_method', 'status', 'transaction_id', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('transaction_id', 'notes')
    list_editable = ('status',)

class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'payment', 'issued_by', 'issued_at')
    list_filter = ('issued_at',)
    search_fields = ('receipt_number', 'payment__transaction_id')
    readonly_fields = ('receipt_number', 'issued_at')

class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'image_preview', 'is_active', 'display_order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'alt_text', 'description')
    list_editable = ('is_active', 'display_order')
    readonly_fields = ('image_preview',)
    fieldsets = (
        ('Advertisement Details', {
            'fields': ('title', 'image', 'image_preview')
        }),
        ('Content', {
            'fields': ('description',),
            'description': 'Add description text for advertisement panels'
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_order', 'link_url', 'alt_text', 'background_color')
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="width: 200px; height: auto;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'

class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'thumbnail_preview', 'is_active', 'display_order', 'created_at')
    list_filter = ('section', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    list_editable = ('is_active', 'display_order')
    readonly_fields = ('thumbnail_preview',)
    fieldsets = (
        ('Video Details', {
            'fields': ('title', 'section', 'description')
        }),
        ('Video Content', {
            'fields': ('video_file', 'video_url', 'thumbnail', 'thumbnail_preview')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_order')
        }),
    )
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="width: 200px; height: auto;" />', obj.thumbnail.url)
        return "No Thumbnail"
    thumbnail_preview.short_description = 'Thumbnail Preview'

class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('title', 'image_preview', 'is_active', 'display_order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    list_editable = ('is_active', 'display_order')
    readonly_fields = ('image_preview',)
    fieldsets = (
        ('Newsletter Details', {
            'fields': ('title', 'description', 'image', 'image_preview')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_order', 'link_url', 'alt_text')
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="width: 200px; height: auto;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'

class FeaturedProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'title', 'image_preview', 'is_active', 'display_order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('product__name', 'title')
    list_editable = ('is_active', 'display_order')
    readonly_fields = ('image_preview',)
    fieldsets = (
        ('Product Details', {
            'fields': ('product', 'title', 'description')
        }),
        ('Featured Image', {
            'fields': ('image', 'image_preview')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_order')
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="width: 200px; height: auto;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'

class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'logo_preview', 'is_active', 'display_order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active', 'display_order')
    readonly_fields = ('logo_preview',)
    fieldsets = (
        ('Brand Details', {
            'fields': ('name', 'description', 'logo', 'logo_preview')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_order', 'link_url', 'alt_text')
        }),
    )
    
    def logo_preview(self, obj):
        if obj.logo:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="width: 200px; height: auto;" />', obj.logo.url)
        return "No Logo"
    logo_preview.short_description = 'Logo Preview'

# Discount and Sales Management Admin Classes

class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_type', 'discount_value_display', 'applies_to', 'is_active', 'is_valid', 'start_date', 'end_date')
    list_filter = ('discount_type', 'applies_to', 'is_active', 'start_date', 'end_date')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    filter_horizontal = ('products', 'categories')
    readonly_fields = ('get_discount_value_display', 'is_valid', 'usage_count')
    fieldsets = (
        ('Discount Information', {
            'fields': ('name', 'description', 'discount_type', 'discount_value', 'get_discount_value_display')
        }),
        ('Applicability', {
            'fields': ('applies_to', 'products', 'categories')
        }),
        ('Date Constraints', {
            'fields': ('start_date', 'end_date')
        }),
        ('Usage Constraints', {
            'fields': ('min_purchase_amount', 'max_discount_amount', 'usage_limit', 'usage_count')
        }),
        ('Status', {
            'fields': ('is_active', 'is_valid')
        }),
    )
    
    def discount_value_display(self, obj):
        return obj.get_discount_value_display()
    discount_value_display.short_description = 'Discount'
    
    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Currently Valid'

class FlashSaleAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_percentage', 'is_active', 'is_active_now', 'is_sold_out', 'start_time', 'end_time', 'sold_count', 'products_count')
    list_filter = ('is_active', 'start_time', 'end_time')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    filter_horizontal = ('products',)
    readonly_fields = ('is_active_now', 'is_sold_out', 'sold_count', 'products_count')
    fieldsets = (
        ('Flash Sale Information', {
            'fields': ('name', 'description', 'discount_percentage')
        }),
        ('Products', {
            'fields': ('products', 'products_count')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time')
        }),
        ('Stock Limits', {
            'fields': ('max_quantity_per_customer', 'total_stock_limit', 'sold_count', 'is_sold_out')
        }),
        ('Popup Styling', {
            'fields': ('background_color',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_active_now')
        }),
    )
    
    def is_active_now(self, obj):
        return obj.is_active_now()
    is_active_now.boolean = True
    is_active_now.short_description = 'Currently Active'
    
    def is_sold_out(self, obj):
        return obj.is_sold_out()
    is_sold_out.boolean = True
    is_sold_out.short_description = 'Sold Out'
    
    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'Products Count'

class OfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'offer_type', 'is_active', 'is_valid', 'start_date', 'end_date')
    list_filter = ('offer_type', 'is_active', 'start_date', 'end_date')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    filter_horizontal = ('products', 'categories')
    readonly_fields = ('is_valid',)
    fieldsets = (
        ('Offer Information', {
            'fields': ('name', 'description', 'offer_type')
        }),
        ('Products & Categories', {
            'fields': ('products', 'categories')
        }),
        ('Offer Parameters', {
            'fields': ('buy_quantity', 'get_quantity', 'discount_percentage', 'gift_product', 'min_purchase_amount')
        }),
        ('Timing', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('is_active', 'is_valid')
        }),
    )
    
    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Currently Valid'

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(MpesaConfiguration, MpesaConfigurationAdmin)
admin.site.register(MpesaTransaction, MpesaTransactionAdmin)
admin.site.register(Banner, BannerAdmin)
admin.site.register(Advertisement, AdvertisementAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(Newsletter, NewsletterAdmin)
admin.site.register(FeaturedProduct, FeaturedProductAdmin)
admin.site.register(Brand, BrandAdmin)

# Register Discount and Sales Management Models
admin.site.register(Discount, DiscountAdmin)
admin.site.register(FlashSale, FlashSaleAdmin)
admin.site.register(Offer, OfferAdmin)

# Register Service Booking and Technician Management Models
admin.site.register(Service, ServiceAdmin)
admin.site.register(ServiceHeroSlide, ServiceHeroSlideAdmin)
admin.site.register(Technician, TechnicianAdmin)
admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(VehicleLog, VehicleLogAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Quotation, QuotationAdmin)
admin.site.register(QuotationItem, QuotationItemAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Receipt, ReceiptAdmin)

# Register new technician models
class ClockInLogAdmin(admin.ModelAdmin):
    list_display = ('technician', 'booking', 'clock_in_time', 'clock_out_time', 'hours_worked', 'date')
    list_filter = ('date', 'technician')
    search_fields = ('technician__user__username', 'notes')
    readonly_fields = ('hours_worked',)

class SiteImageAdmin(admin.ModelAdmin):
    list_display = ('booking', 'image_preview', 'caption', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at', 'booking')
    search_fields = ('caption', 'booking__customer__username')
    readonly_fields = ('image_preview', 'uploaded_at')
    
    def image_preview(self, obj):
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="width: 200px; height: auto;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'

admin.site.register(ClockInLog, ClockInLogAdmin)
admin.site.register(SiteImage, SiteImageAdmin)

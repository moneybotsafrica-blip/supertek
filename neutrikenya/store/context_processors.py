from .models import Cart, SiteSettings, FlashSale

def cart_processor(request):
    """Add cart to context data for all templates."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.get('session_id')
        if session_id:
            try:
                cart = Cart.objects.get(session_id=session_id)
            except Cart.DoesNotExist:
                cart = None
        else:
            cart = None
    
    return {'cart': cart}

def site_settings_processor(request):
    """Add site settings to context data for all templates."""
    settings = SiteSettings.get_settings()
    
    # Get active flash sale
    active_flash_sale = None
    try:
        active_flash_sale = FlashSale.objects.filter(is_active=True).first()
    except:
        pass
    
    return {
        'site_settings': settings,
        'site_logo': settings.logo.url if settings.logo else None,
        'site_favicon': settings.favicon.url if settings.favicon else None,
        'site_name': settings.site_name,
        'contact_email': settings.contact_email,
        'contact_phone': settings.contact_phone,
        'whatsapp_number': settings.whatsapp_number,
        'site_address': settings.address,
        'footer_bg_color': settings.footer_background_color,
        'footer_heading_color': settings.footer_heading_color,
        'header_message_1': settings.header_message_1,
        'header_message_2': settings.header_message_2,
        'footer_about_text': settings.footer_about_text,
        'active_flash_sale': active_flash_sale,
        'enable_promo_popup': settings.enable_promo_popup,
        'promo_title': settings.promo_title,
        'promo_message': settings.promo_message,
        'promo_background_color': settings.promo_background_color,
        'promo_button_text': settings.promo_button_text,
        'promo_button_color': settings.promo_button_color,
    } 
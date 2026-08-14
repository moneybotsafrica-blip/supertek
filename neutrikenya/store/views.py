from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.signals import user_logged_in
from django.contrib import messages
from django.dispatch import receiver
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.contrib.auth.views import LoginView
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Brand, Banner, Advertisement, Service, ServiceHeroSlide, Technician, Booking, Quotation, MpesaTransaction, ClockInLog, SiteImage, Vehicle
from .forms import SignUpForm, UserProfileForm
from .mpesa_service import MpesaService
from .document_generator import DocumentGenerator
import uuid
import json

class CustomLoginView(LoginView):
    """Custom login view that redirects based on user type"""
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        # Check if user is a technician (regardless of admin access)
        if hasattr(self.request.user, 'technician_profile'):
            # If technician has staff status or admin access, redirect to technician admin dashboard
            if self.request.user.is_staff or self.request.user.technician_profile.has_admin_access:
                return reverse('store:technician_admin_dashboard')
            # Otherwise redirect to regular technician dashboard
            return reverse('store:technician_dashboard')
        # Check if user is regular staff (not technician)
        if self.request.user.is_staff:
            return reverse('admin:index')
        # For regular customers, redirect to home/shop
        return reverse('store:home')

@login_required
def technician_admin_dashboard(request):
    """Custom admin dashboard for technicians with admin access"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    technician = request.user.technician_profile
    
    # Get bookings data
    assigned_bookings = technician.get_assigned_bookings()
    all_bookings = Booking.objects.filter(technician=technician).order_by('-created_at')
    completed_count = all_bookings.filter(status='completed').count()
    pending_count = all_bookings.filter(status='assigned').count()
    
    # Get sales data
    from django.db.models import Sum
    from django.db.models.functions import TruncMonth
    
    completed_bookings = all_bookings.filter(status='completed', payment_status='paid')
    total_revenue = completed_bookings.aggregate(
        total=Sum('payment_amount')
    )['total'] or 0
    
    # Use created_at instead of completed_at since that field doesn't exist
    monthly_earnings = completed_bookings.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('payment_amount')
    ).order_by('-month')
    
    # Get vehicle data
    vehicles = Vehicle.objects.filter(assigned_technician=technician, is_active=True)
    
    # Get recent activity
    recent_bookings = all_bookings[:5]
    
    context = {
        'technician': technician,
        'assigned_bookings': assigned_bookings,
        'all_bookings': all_bookings,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'total_revenue': total_revenue,
        'monthly_earnings': monthly_earnings,
        'vehicles': vehicles,
        'recent_bookings': recent_bookings,
        'title': 'Technician Admin Dashboard'
    }
    return render(request, 'store/technician_admin_dashboard.html', context)

def get_or_create_cart(request):
    """Create or retrieve a cart for the user."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['session_id'] = session_id
        
        cart, created = Cart.objects.get_or_create(session_id=session_id)
    
    return cart

def home(request):
    """Home page view showing featured products and categories."""
    featured_products = Product.objects.filter(featured=True, is_available=True)[:8]
    customer_favorites = Product.objects.filter(is_available=True).order_by('?')[:4]
    camping_essentials = Product.objects.filter(category__name__icontains='Camping', is_available=True)[:4]
    bbq_products = Product.objects.filter(category__name__icontains='BBQ', is_available=True)[:4]
    technology_products = Product.objects.filter(
        category__name__in=['Printers & Office Equipment', 'POS Systems', 'Scanners & Mobile Computers', 'Projectors', 'Tablets & Accessories'],
        is_available=True
    )[:8]
    main_categories = Category.objects.filter(parent=None)
    brands = Brand.objects.filter(is_active=True).order_by('display_order', 'name')
    
    context = {
        'featured_products': featured_products,
        'customer_favorites': customer_favorites,
        'camping_essentials': camping_essentials,
        'bbq_products': bbq_products,
        'technology_products': technology_products,
        'main_categories': main_categories,
        'brands': brands,
    }
    return render(request, 'store/home.html', context)

def shop(request):
    """Shop page showing all available products."""
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.filter(parent=None)
    
    # Filter by category if specified
    category_slug = request.GET.get('category')
    current_category = None
    if category_slug:
        try:
            current_category = Category.objects.get(slug=category_slug)
            products = products.filter(
                Q(category=current_category) | Q(category__parent=current_category)
            )
        except Category.DoesNotExist:
            pass
    
    # Get recommended products based on current category
    recommended_products = []
    if current_category:
        # Get products from the same category (excluding current page products)
        recommended_products = Product.objects.filter(
            category=current_category,
            is_available=True
        ).exclude(id__in=products.values_list('id', flat=True))[:4]
    else:
        # If no category selected, show random featured products
        recommended_products = Product.objects.filter(
            is_available=True,
            featured=True
        )[:4]
    
    context = {
        'products': products,
        'categories': categories,
        'recommended_products': recommended_products,
        'current_category': current_category,
        'brands': Brand.objects.filter(is_active=True)[:4],
        'advertisements': Advertisement.objects.filter(is_active=True).order_by('display_order')[:5],
        'bestseller_banner': Banner.objects.filter(
            banner_type='bestseller', 
            is_active=True,
            category=current_category
        ).first() if current_category else Banner.objects.filter(
            banner_type='bestseller', 
            is_active=True,
            category__isnull=True
        ).first(),
    }
    return render(request, 'store/shop.html', context)

def category_detail(request, slug):
    """Category page showing all products in a category."""
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(
        Q(category=category) | Q(category__parent=category),
        is_available=True
    )
    subcategories = category.subcategories.all()
    
    context = {
        'category': category,
        'products': products,
        'subcategories': subcategories,
    }
    return render(request, 'store/category_detail.html', context)

def product_detail(request, slug):
    """Product detail page."""
    product = get_object_or_404(Product, slug=slug, is_available=True)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'store/product_detail.html', context)

def add_to_cart(request, product_id):
    """Add a product to the cart."""
    product = get_object_or_404(Product, id=product_id, is_available=True)
    cart = get_or_create_cart(request)
    
    # Always set quantity to 1
    quantity = 1
    
    # Use get_or_create to prevent duplicate items
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        # Item already exists, just update quantity to 1
        cart_item.quantity = quantity
        cart_item.save()
    
    messages.success(request, f"{product.name} added to your cart.")
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'item_count': cart.item_count,
            'total_price': cart.total_price,
        })
    
    return redirect('store:product_detail', slug=product.slug)

def update_cart_item(request, item_id):
    """Update quantity of a cart item."""
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Ensure the cart belongs to the user
    cart = get_or_create_cart(request)
    if cart_item.cart.id != cart.id:
        messages.error(request, "You don't have permission to update this item.")
        return redirect('store:cart')
    
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'item_count': cart.item_count,
            'total_price': cart.total_price,
        })
    
    return redirect('store:cart')

def remove_from_cart(request, item_id):
    """Remove an item from the cart."""
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Ensure the cart belongs to the user
    cart = get_or_create_cart(request)
    if cart_item.cart.id != cart.id:
        messages.error(request, "You don't have permission to remove this item.")
        return redirect('store:cart')
    
    cart_item.delete()
    messages.success(request, "Item removed from your cart.")
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'item_count': cart.item_count,
            'total_price': cart.total_price,
        })
    
    return redirect('store:cart')

def cart_view(request):
    """View cart contents."""
    cart = get_or_create_cart(request)
    context = {'cart': cart}
    return render(request, 'store/cart.html', context)

def checkout(request):
    """Checkout page."""
    cart = get_or_create_cart(request)
    
    if cart.item_count == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('store:cart')
    
    context = {'cart': cart}
    return render(request, 'store/checkout.html', context)

def place_order(request):
    """Process order placement."""
    if request.method != 'POST':
        return redirect('store:checkout')
    
    cart = get_or_create_cart(request)
    
    if cart.item_count == 0:
        error_msg = "Your cart is empty."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.warning(request, error_msg)
        return redirect('store:cart')
    
    # Get form data
    payment_method = request.POST.get('payment_method', 'mpesa')
    
    # For M-Pesa, initiate payment first before creating order
    if payment_method == 'mpesa':
        mpesa_phone = request.POST.get('mpesa_phone')
        
        if not mpesa_phone:
            error_msg = "Please provide your M-Pesa phone number."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return redirect('store:checkout')
        
        # Store M-Pesa phone number for logged in users
        if mpesa_phone and request.user.is_authenticated:
            profile = request.user.profile
            profile.mpesa_phone = mpesa_phone
            profile.default_payment_method = 'mpesa'
            profile.save()
        
        # Initiate M-Pesa STK push first
        try:
            mpesa_service = MpesaService()
            callback_url = request.build_absolute_uri(reverse('store:mpesa_callback'))
            
            # Create order first with pending status
            order = Order(
                user=request.user if request.user.is_authenticated else None,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                address=request.POST.get('address'),
                city=request.POST.get('city'),
                payment_method=payment_method,
                status='pending_payment',  # Changed to pending_payment
                delivery_instructions=request.POST.get('delivery_instructions', '')
            )
            order.save()
            
            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    price=cart_item.product.price,
                    quantity=cart_item.quantity
                )
            
            # Calculate total amount from cart (not from order property)
            total_amount = cart.total_price
            
            # Now initiate M-Pesa payment
            result = mpesa_service.initiate_stk_push(
                phone_number=mpesa_phone or order.phone,
                amount=int(total_amount),
                order_id=order.id,
                callback_url=callback_url
            )
            
            if result.get('success'):
                success_msg = "Order created! Please check your phone and enter your M-Pesa PIN to complete payment."
                # Clear cart only after successful payment initiation
                cart.items.all().delete()
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'redirect_url': reverse('store:order_confirmation', kwargs={'order_id': order.id})
                    })
                
                messages.success(request, success_msg)
                return redirect('store:order_confirmation', order_id=order.id)
            else:
                # Payment initiation failed, delete the order
                order.delete()
                error_msg = "Unable to proceed with payment. Please try again."
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                
                messages.error(request, error_msg)
                return redirect('store:checkout')
                
        except ValueError as e:
            print(f"M-Pesa configuration error: {e}")  # Log technical error
            # Check if it's a callback URL issue
            if "CallBackURL" in str(e) or "localhost" in str(e) or "127.0.0.1" in str(e):
                error_msg = "Payment system configuration error. Please contact support."
            else:
                error_msg = "Unable to proceed with payment. Please try again."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return redirect('store:checkout')
        except Exception as e:
            print(f"Error initiating M-Pesa payment: {e}")
            import traceback
            traceback.print_exc()
            error_msg = "Unable to proceed with payment. Please try again."
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            
            messages.error(request, error_msg)
            return redirect('store:checkout')
    
    # For other payment methods, process normally
    else:
        # Create order
        order = Order(
            user=request.user if request.user.is_authenticated else None,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            payment_method=payment_method,
            status='pending',
            delivery_instructions=request.POST.get('delivery_instructions', '')
        )
        order.save()
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                price=cart_item.product.price,
                quantity=cart_item.quantity
            )
        
        # Store payment info if needed
        if payment_method == 'card':
            # Store last 4 digits of card for reference
            card_number = request.POST.get('card_number', '')
            if card_number and request.user.is_authenticated:
                # Only store last 4 digits for security
                last_four = card_number[-4:] if len(card_number) >= 4 else ''
                profile = request.user.profile
                profile.card_last_four = last_four
                profile.card_expiry = request.POST.get('card_expiry', '')
                profile.default_payment_method = 'card'
                profile.save()
        
        # Clear cart
        cart.items.all().delete()
        
        success_msg = "Your order has been placed successfully!"
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('store:order_confirmation', kwargs={'order_id': order.id})
            })
        
        messages.success(request, success_msg)
        return redirect('store:order_confirmation', order_id=order.id)

def order_confirmation(request, order_id):
    """Order confirmation page."""
    order = get_object_or_404(Order, id=order_id)
    
    # Security check to ensure order belongs to user or is accessible via session
    if request.user.is_authenticated:
        if order.user and order.user != request.user:
            messages.error(request, "You don't have permission to view this order.")
            return redirect('store:home')
    
    context = {'order': order}
    return render(request, 'store/order_confirmation.html', context)

def about(request):
    """About page."""
    return render(request, 'store/about.html', {})

def contact(request):
    """Contact page."""
    return render(request, 'store/contact.html')

def signup(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in after registration
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "Registration successful! Welcome to Mustek East Africa.")
            return redirect('store:home')
    else:
        form = SignUpForm()
    
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def profile(request):
    """Display user profile and order history."""
    # Handle form submission
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('store:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    # Get user's orders
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Determine if user has all required info for checkout
    profile_complete = False
    payment_complete = False
    if hasattr(request.user, 'profile'):
        profile = request.user.profile
        profile_complete = profile.has_complete_shipping_info()
        payment_complete = profile.has_complete_payment_info()
    
    context = {
        'user': request.user,
        'form': form,
        'orders': orders,
        'profile_complete': profile_complete,
        'payment_complete': payment_complete,
        'active_tab': request.GET.get('tab', 'profile')  # Default to profile tab
    }
    return render(request, 'store/profile.html', context)

@login_required
def order_detail(request, order_id):
    """Display details of a specific order."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order
    }
    return render(request, 'store/order_detail.html', context)

@receiver(user_logged_in)
def redirect_on_login(sender, user, request, **kwargs):
    """
    Redirect users based on their type after login.
    Technicians go to technician dashboard, customers go to home.
    """
    # This is a backup redirect mechanism in case the CustomLoginView doesn't handle it
    from django.urls import reverse
    
    if hasattr(user, 'technician_profile'):
        # Set session variable to indicate technician login
        request.session['user_type'] = 'technician'
    else:
        request.session['user_type'] = 'customer'

@receiver(user_logged_in)
def merge_carts_on_login(sender, user, request, **kwargs):
    """
    When a user logs in, if they have items in a session-based cart,
    transfer those items to their user account cart.
    """
    session_id = request.session.get('session_id')
    if not session_id:
        return
    
    try:
        # Get the session cart
        session_cart = Cart.objects.get(session_id=session_id)
        
        # Check if the user already has a cart
        try:
            user_cart = Cart.objects.get(user=user)
            
            # Transfer items from session cart to user cart
            for session_item in session_cart.items.all():
                try:
                    # Check if the product already exists in the user's cart
                    user_item = CartItem.objects.get(cart=user_cart, product=session_item.product)
                    # If it exists, update the quantity
                    user_item.quantity += session_item.quantity
                    user_item.save()
                except CartItem.DoesNotExist:
                    # If it doesn't exist, create a new cart item in the user's cart
                    session_item.cart = user_cart
                    session_item.save()
            
            # Delete the session cart after transferring items
            session_cart.delete()
            
        except Cart.DoesNotExist:
            # If the user doesn't have a cart, simply assign the session cart to the user
            session_cart.user = user
            session_cart.save()
            
        # Clear the session ID
        del request.session['session_id']
        
    except Cart.DoesNotExist:
        # No session cart exists
        pass

# Service Booking Views

def services(request):
    """Display all available services"""
    services = Service.objects.filter(is_active=True).order_by('name')
    hero_slides = ServiceHeroSlide.objects.filter(is_active=True).order_by('display_order', '-created_at')
    context = {
        'services': services,
        'hero_slides': hero_slides,
        'title': 'Our Services - Installations & Repairs'
    }
    return render(request, 'store/services.html', context)

def service_detail(request, slug):
    """Display individual service details"""
    service = get_object_or_404(Service, slug=slug, is_active=True)
    context = {
        'service': service,
        'title': f'{service.name} - Service Details'
    }
    return render(request, 'store/service_detail.html', context)

@login_required
def book_service(request, service_slug):
    """Book a service with M-Pesa payment"""
    service = get_object_or_404(Service, slug=service_slug, is_active=True)
    
    if request.method == 'POST':
        # Process booking form
        scheduled_date = request.POST.get('scheduled_date')
        address = request.POST.get('address')
        city = request.POST.get('city')
        phone = request.POST.get('phone')
        notes = request.POST.get('notes', '')
        mpesa_phone = request.POST.get('mpesa_phone')
        
        # Calculate callout fee with VAT
        from decimal import Decimal
        callout_fee = service.callout_fee
        vat_rate = Decimal('0.16')
        vat_amount = callout_fee * vat_rate
        total_amount = callout_fee + vat_amount
        
        # Create booking first (pending payment)
        booking = Booking.objects.create(
            service=service,
            customer=request.user,
            scheduled_date=scheduled_date,
            address=address,
            city=city,
            phone=phone,
            notes=notes,
            status='pending',
            payment_status='pending',
            payment_amount=total_amount,
            payment_method='mpesa'
        )
        
        # Initiate M-Pesa payment
        try:
            mpesa_service = MpesaService()
            callback_url = request.build_absolute_uri(reverse('store:mpesa_callback'))
            
            result = mpesa_service.initiate_stk_push(
                phone_number=mpesa_phone or phone,
                amount=int(total_amount),
                order_id=booking.id,  # Use booking ID as reference
                callback_url=callback_url,
                is_booking=True  # Mark this as a booking payment
            )
            
            if result.get('success'):
                messages.success(request, "Booking created successfully! Please check your phone and enter your M-Pesa PIN to complete payment.")
                return redirect('store:booking_confirmation', booking_id=booking.id)
            else:
                messages.warning(request, f"Booking created but payment initiation failed: {result.get('error', 'Unknown error')}. You can try paying from the booking confirmation page.")
                return redirect('store:booking_confirmation', booking_id=booking.id)
                
        except ValueError as e:
            messages.warning(request, f"Booking created but M-Pesa service is not configured: {str(e)}. You can try paying later.")
            return redirect('store:booking_confirmation', booking_id=booking.id)
        except Exception as e:
            print(f"Error initiating M-Pesa payment: {e}")
            import traceback
            traceback.print_exc()
            messages.warning(request, "Booking created but there was an error initiating payment. You can try paying from the booking confirmation page.")
            return redirect('store:booking_confirmation', booking_id=booking.id)
    
    context = {
        'service': service,
        'title': f'Book {service.name}'
    }
    return render(request, 'store/book_service.html', context)

@login_required
def booking_confirmation(request, booking_id):
    """Display booking confirmation"""
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    context = {
        'booking': booking,
        'total_cost': booking.get_total_cost(),
        'title': 'Booking Confirmed'
    }
    return render(request, 'store/booking_confirmation.html', context)

@login_required
def process_booking_payment(request, booking_id):
    """Process M-Pesa payment for booking"""
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    
    if request.method == 'POST':
        mpesa_phone = request.POST.get('mpesa_phone')
        
        # Calculate callout fee with VAT
        from decimal import Decimal
        callout_fee = booking.service.callout_fee
        vat_rate = Decimal('0.16')
        vat_amount = callout_fee * vat_rate
        total_amount = callout_fee + vat_amount
        
        # Initiate M-Pesa payment (placeholder for actual API integration)
        try:
            # TODO: Integrate with actual M-Pesa Daraja API
            # For now, we'll simulate payment processing
            payment_success = True  # This should be the result of M-Pesa API call
            
            if payment_success:
                # Update booking payment status
                booking.payment_status = 'paid'
                booking.payment_amount = total_amount
                booking.payment_method = 'mpesa'
                booking.save()
                
                # Auto-assign technician if not already assigned
                if not booking.technician:
                    available_technicians = Technician.objects.filter(
                        skills=booking.service,
                        is_available=True
                    ).order_by('-rating', '-total_jobs')
                    
                    if available_technicians.exists():
                        booking.technician = available_technicians.first()
                        booking.status = 'assigned'
                        booking.save()
                        
                        # Send email notification to technician
                        try:
                            subject = f'New Service Booking - {booking.service.name}'
                            context = {
                                'technician_name': booking.technician.user.get_full_name(),
                                'booking_id': booking.id,
                                'service_name': booking.service.name,
                                'service_type': booking.service.get_service_type_display(),
                                'scheduled_date': booking.scheduled_date.strftime('%B %d, %Y at %I:%M %p'),
                                'city': booking.city,
                                'address': booking.address,
                                'customer_name': request.user.get_full_name(),
                                'customer_phone': booking.phone,
                                'customer_email': request.user.email,
                                'notes': booking.notes,
                                'service_fee': booking.service.base_price,
                                'callout_fee': booking.service.callout_fee,
                                'vat_amount': (booking.service.base_price + booking.service.callout_fee) * 0.16,
                                'total_amount': booking.get_total_cost(),
                                'booking_url': request.build_absolute_uri(reverse('store:booking_confirmation', kwargs={'booking_id': booking.id})),
                            }
                            html_content = render_to_string('emails/technician_notification.html', context)
                            
                            email = EmailMultiAlternatives(
                                subject,
                                html_content,
                                settings.DEFAULT_FROM_EMAIL,
                                [booking.technician.user.email],
                            )
                            email.content_subtype = 'html'
                            email.send()
                            print(f"Technician email sent to {booking.technician.user.email}")
                        except Exception as e:
                            print(f"Error sending technician email: {e}")
                            import traceback
                            traceback.print_exc()
                
                # Send confirmation email to customer
                try:
                    total_cost = booking.get_total_cost()
                    subject = f'Payment Confirmed - {booking.service.name}'
                    context = {
                        'customer_name': request.user.get_full_name(),
                        'booking_id': booking.id,
                        'service_name': booking.service.name,
                        'service_type': booking.service.get_service_type_display(),
                        'scheduled_date': booking.scheduled_date.strftime('%B %d, %Y at %I:%M %p'),
                        'city': booking.city,
                        'address': booking.address,
                        'phone': booking.phone,
                        'status': booking.get_status_display(),
                        'technician_name': booking.technician.user.get_full_name() if booking.technician else 'To be assigned',
                        'service_fee': booking.service.base_price,
                        'callout_fee': booking.service.callout_fee,
                        'vat_amount': vat_amount,
                        'total_amount': total_cost,
                        'booking_url': request.build_absolute_uri(reverse('store:booking_confirmation', kwargs={'booking_id': booking.id})),
                    }
                    html_content = render_to_string('emails/booking_confirmation.html', context)
                    
                    email = EmailMultiAlternatives(
                        subject,
                        html_content,
                        settings.DEFAULT_FROM_EMAIL,
                        [request.user.email],
                    )
                    email.content_subtype = 'html'
                    email.send()
                    print(f"Payment confirmation email sent to {request.user.email}")
                    messages.success(request, "Payment successful! A confirmation email has been sent to your email address.")
                except Exception as e:
                    print(f"Error sending customer email: {e}")
                    import traceback
                    traceback.print_exc()
                    messages.success(request, "Payment successful! Your booking is now confirmed.")
                
                return redirect('store:booking_confirmation', booking_id=booking.id)
            else:
                messages.error(request, "Payment failed. Please try again or contact support.")
                return redirect('store:booking_confirmation', booking_id=booking.id)
                
        except Exception as e:
            print(f"Error processing payment: {e}")
            import traceback
            traceback.print_exc()
            messages.error(request, "An error occurred during payment processing. Please try again.")
            return redirect('store:booking_confirmation', booking_id=booking.id)
    
    return redirect('store:booking_confirmation', booking_id=booking_id)

@login_required
def my_bookings(request):
    """Display customer's bookings"""
    bookings = Booking.objects.filter(customer=request.user).order_by('-created_at')
    completed_count = bookings.filter(status='completed').count()
    pending_count = bookings.filter(status='pending').count()
    in_progress_count = bookings.filter(status='in_progress').count()
    
    context = {
        'bookings': bookings,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'title': 'My Bookings'
    }
    return render(request, 'store/my_bookings.html', context)

@login_required
def api_booking_details(request, booking_id):
    """API endpoint to get booking details for modal"""
    if not hasattr(request.user, 'technician_profile'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    booking = get_object_or_404(Booking, id=booking_id, technician=request.user.technician_profile)
    
    return JsonResponse({
        'customer_name': booking.customer.get_full_name(),
        'phone': booking.phone,
        'address': booking.address,
        'city': booking.city,
        'service': booking.service.name,
        'scheduled_date': booking.scheduled_date.strftime('%Y-%m-%d %H:%M'),
        'status': booking.get_status_display(),
        'payment_status': booking.get_payment_status_display(),
        'notes': booking.notes
    })

@login_required
def create_quotation(request, booking_id):
    """Create quotation for a booking"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    booking = get_object_or_404(Booking, id=booking_id, technician=request.user.technician_profile)
    products = Product.objects.filter(is_available=True).order_by('name')
    
    if request.method == 'POST':
        # Create quotation
        from datetime import timedelta
        valid_until = timezone.now() + timedelta(days=30)
        
        quotation = Quotation.objects.create(
            booking=booking,
            labor_cost=float(request.POST.get('labor_cost', 0)),
            parts_cost=float(request.POST.get('parts_cost', 0)),
            notes=request.POST.get('notes', ''),
            valid_until=valid_until,
            status='draft'
        )
        
        # Add quotation items
        item_descriptions = request.POST.getlist('item_description[]')
        item_quantities = request.POST.getlist('item_quantity[]')
        item_prices = request.POST.getlist('item_price[]')
        item_products = request.POST.getlist('item_product[]')
        
        for i, desc in enumerate(item_descriptions):
            if desc and i < len(item_quantities) and i < len(item_prices):
                product_id = item_products[i] if i < len(item_products) else None
                product = Product.objects.filter(id=product_id).first() if product_id else None
                
                QuotationItem.objects.create(
                    quotation=quotation,
                    description=desc,
                    quantity=int(item_quantities[i]),
                    unit_price=float(item_prices[i]),
                    product=product
                )
        
        return redirect('store:view_quotation', quotation_id=quotation.id)
    
    context = {
        'booking': booking,
        'products': products,
        'title': f'Create Quotation - Booking #{booking.id}'
    }
    return render(request, 'store/create_quotation.html', context)

@login_required
def view_quotation(request, quotation_id):
    """View quotation template"""
    quotation = get_object_or_404(Quotation, id=quotation_id)
    
    # Check if user is authorized (technician or customer)
    if not (request.user == quotation.booking.customer or 
            (hasattr(request.user, 'technician_profile') and 
             request.user.technician_profile == quotation.booking.technician)):
        return redirect('store:home')
    
    from store.models import SiteSettings
    site_settings = SiteSettings.get_settings()
    
    context = {
        'quotation': quotation,
        'booking': quotation.booking,
        'site_settings': site_settings,
        'title': f'Quotation {quotation.quotation_number}'
    }
    return render(request, 'store/quotation_template.html', context)

@login_required
def update_booking_status(request, booking_id):
    """Update booking status (technician only)"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    booking = get_object_or_404(Booking, id=booking_id, technician=request.user.technician_profile)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status in dict(Booking.STATUS_CHOICES):
            booking.status = new_status
            booking.notes = notes
            booking.save()
            
            # Update technician performance metrics
            if new_status == 'completed':
                technician = request.user.technician_profile
                technician.total_jobs += 1
                technician.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, "Booking status updated successfully.")
        return redirect('store:technician_admin_dashboard')
    
    context = {
        'booking': booking,
        'status_choices': Booking.STATUS_CHOICES,
        'title': f'Update Status - Booking #{booking.id}'
    }
    return render(request, 'store/update_booking_status.html', context)

@login_required
def complete_job(request, booking_id):
    """Mark job as completed and create payment (technician only)"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    booking = get_object_or_404(Booking, id=booking_id, technician=request.user.technician_profile)
    
    if request.method == 'POST':
        booking.status = 'completed'
        booking.completed_at = timezone.now()
        booking.save()
        
        # Update technician performance metrics
        technician = request.user.technician_profile
        technician.total_jobs += 1
        technician.save()
        
        messages.success(request, "Job marked as completed successfully.")
        return redirect('store:technician_admin_dashboard')
    
    context = {
        'booking': booking,
        'title': f'Complete Job - Booking #{booking.id}'
    }
    return render(request, 'store/complete_job.html', context)

@login_required
def technician_quotations(request):
    """View all quotations created by technician"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    technician = request.user.technician_profile
    quotations = Quotation.objects.filter(
        booking__technician=technician
    ).order_by('-created_at')
    
    context = {
        'quotations': quotations,
        'title': 'My Quotations'
    }
    return render(request, 'store/technician_quotations.html', context)

@login_required
def edit_quotation(request, quotation_id):
    """Edit existing quotation"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    quotation = get_object_or_404(Quotation, id=quotation_id, booking__technician=request.user.technician_profile)
    products = Product.objects.filter(is_available=True).order_by('name')
    
    if quotation.status != 'draft':
        messages.error(request, "Can only edit draft quotations.")
        return redirect('store:view_quotation', quotation_id=quotation.id)
    
    if request.method == 'POST':
        # Update quotation
        quotation.labor_cost = float(request.POST.get('labor_cost', quotation.labor_cost))
        quotation.parts_cost = float(request.POST.get('parts_cost', quotation.parts_cost))
        quotation.notes = request.POST.get('notes', quotation.notes)
        quotation.save()
        
        # Remove existing items and add new ones
        quotation.items.all().delete()
        
        item_descriptions = request.POST.getlist('item_description[]')
        item_quantities = request.POST.getlist('item_quantity[]')
        item_prices = request.POST.getlist('item_price[]')
        item_products = request.POST.getlist('item_product[]')
        
        for i, desc in enumerate(item_descriptions):
            if desc and i < len(item_quantities) and i < len(item_prices):
                product_id = item_products[i] if i < len(item_products) else None
                product = Product.objects.filter(id=product_id).first() if product_id else None
                
                QuotationItem.objects.create(
                    quotation=quotation,
                    description=desc,
                    quantity=int(item_quantities[i]),
                    unit_price=float(item_prices[i]),
                    product=product
                )
        
        messages.success(request, "Quotation updated successfully.")
        return redirect('store:view_quotation', quotation_id=quotation.id)
    
    context = {
        'quotation': quotation,
        'booking': quotation.booking,
        'products': products,
        'title': f'Edit Quotation - {quotation.quotation_number}'
    }
    return render(request, 'store/edit_quotation.html', context)

@login_required
def send_quotation(request, quotation_id):
    """Send quotation to customer for approval"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    quotation = get_object_or_404(Quotation, id=quotation_id, booking__technician=request.user.technician_profile)
    
    if quotation.status != 'draft':
        messages.error(request, "Can only send draft quotations.")
        return redirect('store:view_quotation', quotation_id=quotation.id)
    
    quotation.status = 'sent'
    quotation.save()
    
    # Send email notification to customer
    try:
        subject = f"Quotation for Service Booking #{quotation.booking.id}"
        message = render_to_string('store/email/quotation_notification.html', {
            'quotation': quotation,
            'booking': quotation.booking,
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [quotation.booking.customer.email],
            fail_silently=True
        )
        
        messages.success(request, "Quotation sent to customer successfully.")
    except Exception as e:
        print(f"Error sending quotation email: {e}")
        messages.warning(request, "Quotation marked as sent but email notification failed.")
    
    return redirect('store:view_quotation', quotation_id=quotation.id)

@login_required
def technician_vehicles(request):
    """View assigned vehicles for technician"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    technician = request.user.technician_profile
    vehicles = Vehicle.objects.filter(assigned_technician=technician, is_active=True)
    
    context = {
        'vehicles': vehicles,
        'title': 'My Vehicles'
    }
    return render(request, 'store/technician_vehicles.html', context)

@login_required
def vehicle_details(request, vehicle_id):
    """View vehicle details and logs"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, assigned_technician=request.user.technician_profile)
    logs = vehicle.logs.order_by('-date')
    
    context = {
        'vehicle': vehicle,
        'logs': logs,
        'title': f'Vehicle Details - {vehicle.registration_number}'
    }
    return render(request, 'store/vehicle_details.html', context)

@login_required
def add_vehicle_log(request, vehicle_id):
    """Add daily mileage log for vehicle"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, assigned_technician=request.user.technician_profile)
    
    if request.method == 'POST':
        from datetime import date
        starting_mileage = int(request.POST.get('starting_mileage'))
        ending_mileage = int(request.POST.get('ending_mileage'))
        distance_traveled = ending_mileage - starting_mileage
        fuel_consumed = request.POST.get('fuel_consumed')
        notes = request.POST.get('notes', '')
        
        VehicleLog.objects.create(
            vehicle=vehicle,
            date=date.today(),
            starting_mileage=starting_mileage,
            ending_mileage=ending_mileage,
            distance_traveled=distance_traveled,
            fuel_consumed=float(fuel_consumed) if fuel_consumed else None,
            notes=notes,
            logged_by=request.user
        )
        
        messages.success(request, "Vehicle log added successfully.")
        return redirect('store:vehicle_details', vehicle_id=vehicle.id)
    
    context = {
        'vehicle': vehicle,
        'title': f'Add Log - {vehicle.registration_number}'
    }
    return render(request, 'store/add_vehicle_log.html', context)

@login_required
def technician_profile(request):
    """View and edit technician profile"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    technician = request.user.technician_profile
    
    if request.method == 'POST':
        # Update technician profile
        technician.phone = request.POST.get('phone', technician.phone)
        technician.is_available = request.POST.get('is_available') == 'on'
        
        # Update user information
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.email = request.POST.get('email', request.user.email)
        
        request.user.save()
        technician.save()
        
        # Update skills
        skill_ids = request.POST.getlist('skills')
        technician.skills.set(skill_ids)
        
        messages.success(request, "Profile updated successfully.")
        return redirect('store:technician_profile')
    
    all_services = Service.objects.all()
    
    context = {
        'technician': technician,
        'all_services': all_services,
        'title': 'My Profile'
    }
    return render(request, 'store/technician_profile.html', context)

@login_required
def technician_calendar(request, year=None, month=None):
    """View technician calendar with bookings"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    from datetime import datetime, timedelta
    import calendar
    
    technician = request.user.technician_profile
    
    # Get current year and month
    today = datetime.now()
    year = int(year) if year else today.year
    month = int(month) if month else today.month
    
    # Get calendar month
    cal = calendar.monthcalendar(year, month)
    
    # Get bookings for the month
    bookings = Booking.objects.filter(
        technician=technician,
        scheduled_date__year=year,
        scheduled_date__month=month
    ).order_by('scheduled_date')
    
    # Create booking dictionary by date
    bookings_by_date = {}
    for booking in bookings:
        date_key = booking.scheduled_date.date()
        if date_key not in bookings_by_date:
            bookings_by_date[date_key] = []
        bookings_by_date[date_key].append(booking)
    
    # Month name and navigation
    month_name = calendar.month_name[month]
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    context = {
        'technician': technician,
        'cal': cal,
        'bookings_by_date': bookings_by_date,
        'month_name': month_name,
        'year': year,
        'month': month,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'title': f'Calendar - {month_name} {year}'
    }
    return render(request, 'store/technician_calendar.html', context)

@login_required
def technician_payments(request):
    """View technician payments and earnings"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    technician = request.user.technician_profile
    
    # Get completed bookings with payments
    completed_bookings = Booking.objects.filter(
        technician=technician,
        status='completed',
        payment_status='paid'
    ).order_by('-updated_at')
    
    # Calculate total earnings
    total_earnings = sum(booking.service.base_price for booking in completed_bookings)
    
    # Calculate earnings by month
    from django.db.models import Sum
    from django.db.models.functions import TruncMonth
    
    monthly_earnings = completed_bookings.annotate(
        month=TruncMonth('updated_at')
    ).values('month').annotate(
        total=Sum('service__base_price')
    ).order_by('-month')
    
    context = {
        'technician': technician,
        'completed_bookings': completed_bookings,
        'total_earnings': total_earnings,
        'monthly_earnings': monthly_earnings,
        'title': 'My Payments'
    }
    return render(request, 'store/technician_payments.html', context)

@login_required
def technician_sales_report(request):
    """View technician sales report and performance metrics"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    technician = request.user.technician_profile
    
    # Get all bookings
    all_bookings = Booking.objects.filter(technician=technician)
    
    # Calculate statistics
    total_bookings = all_bookings.count()
    completed_bookings = all_bookings.filter(status='completed').count()
    pending_bookings = all_bookings.filter(status='assigned').count()
    total_revenue = all_bookings.filter(payment_status='paid').aggregate(
        total=Sum('service__base_price')
    )['total'] or 0
    
    # Calculate average rating
    avg_rating = technician.rating
    
    # Calculate hours worked
    total_hours = technician.get_total_hours_worked()
    
    # Get recent bookings
    recent_bookings = all_bookings.order_by('-created_at')[:10]
    
    # Get service breakdown
    from django.db.models import Count
    service_breakdown = all_bookings.values('service__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'technician': technician,
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'pending_bookings': pending_bookings,
        'total_revenue': total_revenue,
        'avg_rating': avg_rating,
        'total_hours': total_hours,
        'recent_bookings': recent_bookings,
        'service_breakdown': service_breakdown,
        'title': 'Sales Report'
    }
    return render(request, 'store/technician_sales_report.html', context)

@login_required
def clock_in(request, booking_id=None):
    """Clock in for a job"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    technician = request.user.technician_profile
    from datetime import datetime
    
    if request.method == 'POST':
        booking = None
        if booking_id:
            booking = get_object_or_404(Booking, id=booking_id, technician=technician)
        
        # Check if already clocked in today
        from datetime import date
        today = date.today()
        existing_log = ClockInLog.objects.filter(
            technician=technician,
            date=today,
            clock_out_time__isnull=True
        ).first()
        
        if existing_log:
            messages.warning(request, "You are already clocked in. Please clock out first.")
            return redirect('store:technician_admin_dashboard')
        
        # Create clock in log
        ClockInLog.objects.create(
            technician=technician,
            booking=booking,
            clock_in_time=timezone.now(),
            date=today
        )
        
        messages.success(request, "Clocked in successfully.")
        return redirect('store:technician_admin_dashboard')
    
    # Get assigned bookings
    assigned_bookings = technician.get_assigned_bookings()
    
    context = {
        'assigned_bookings': assigned_bookings,
        'title': 'Clock In'
    }
    return render(request, 'store/clock_in.html', context)

@login_required
def clock_out(request):
    """Clock out from current job"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    technician = request.user.technician_profile
    from datetime import date
    
    # Get active clock in
    today = date.today()
    active_log = ClockInLog.objects.filter(
        technician=technician,
        date=today,
        clock_out_time__isnull=True
    ).first()
    
    if not active_log:
        messages.warning(request, "No active clock-in found.")
        return redirect('store:technician_admin_dashboard')
    
    if request.method == 'POST':
        active_log.clock_out_time = timezone.now()
        active_log.calculate_hours()
        active_log.save()
        
        # Update technician total hours
        technician.total_hours = technician.get_total_hours_worked()
        technician.save()
        
        messages.success(request, f"Clocked out successfully. Hours worked: {active_log.hours_worked}")
        return redirect('store:technician_admin_dashboard')
    
    context = {
        'active_log': active_log,
        'title': 'Clock Out'
    }
    return render(request, 'store/clock_out.html', context)

@login_required
def upload_site_image(request, booking_id):
    """Upload site images for a booking"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    booking = get_object_or_404(Booking, id=booking_id, technician=request.user.technician_profile)
    
    if request.method == 'POST':
        caption = request.POST.get('caption', '')
        image_file = request.FILES.get('image')
        
        if image_file:
            SiteImage.objects.create(
                booking=booking,
                image=image_file,
                caption=caption,
                uploaded_by=request.user
            )
            messages.success(request, "Image uploaded successfully.")
        else:
            messages.error(request, "Please select an image to upload.")
        
        return redirect('store:booking_details', booking_id=booking.id)
    
    context = {
        'booking': booking,
        'title': f'Upload Site Images - Booking #{booking.id}'
    }
    return render(request, 'store/upload_site_image.html', context)

@login_required
def booking_details(request, booking_id):
    """View detailed booking information"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    booking = get_object_or_404(Booking, id=booking_id, technician=request.user.technician_profile)
    site_images = booking.site_images.all()
    
    context = {
        'booking': booking,
        'site_images': site_images,
        'title': f'Booking Details - #{booking.id}'
    }
    return render(request, 'store/booking_details.html', context)

@login_required
def print_job_card(request, booking_id):
    """Print job card for a booking"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    booking = get_object_or_404(Booking, id=booking_id, technician=request.user.technician_profile)
    
    context = {
        'booking': booking,
        'title': f'Job Card - #{booking.id}'
    }
    return render(request, 'store/print_job_card.html', context)

@login_required
def print_invoice(request, booking_id):
    """Print invoice for a completed booking"""
    if not hasattr(request.user, 'technician_profile'):
        return redirect('store:home')
    
    booking = get_object_or_404(Booking, id=booking_id, technician=request.user.technician_profile)
    
    from store.models import SiteSettings
    site_settings = SiteSettings.get_settings()
    
    context = {
        'booking': booking,
        'site_settings': site_settings,
        'title': f'Invoice - Booking #{booking.id}'
    }
    return render(request, 'store/print_invoice.html', context)

# M-Pesa Payment Views

@csrf_exempt
def mpesa_callback(request):
    """Handle M-Pesa STK push callback"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST requests allowed'})
    
    try:
        # Parse callback data
        callback_data = json.loads(request.body)
        
        # Process the callback using M-Pesa service
        mpesa_service = MpesaService()
        result = mpesa_service.process_callback(callback_data)
        
        if result.get('success'):
            return JsonResponse({'success': True, 'result_code': result.get('result_code')})
        else:
            return JsonResponse({'success': False, 'error': result.get('error')})
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        print(f"Error in M-Pesa callback: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

def initiate_mpesa_payment(request, order_id):
    """Initiate M-Pesa STK push payment for an order"""
    order = get_object_or_404(Order, id=order_id)
    
    # Security check - ensure order belongs to user or session
    if request.user.is_authenticated:
        if order.user and order.user != request.user:
            messages.error(request, "You don't have permission to pay for this order.")
            return redirect('store:home')
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        
        if not phone_number:
            messages.error(request, "Phone number is required.")
            return redirect('store:order_confirmation', order_id=order.id)
        
        try:
            # Initiate STK push
            mpesa_service = MpesaService()
            
            # Build callback URL
            callback_url = request.build_absolute_uri(reverse('store:mpesa_callback'))
            
            result = mpesa_service.initiate_stk_push(
                phone_number=phone_number,
                amount=int(order.total_price),
                order_id=order.id,
                callback_url=callback_url
            )
            
            if result.get('success'):
                messages.success(request, "Please check your phone and enter your M-Pesa PIN to complete the payment.")
                return redirect('store:order_confirmation', order_id=order.id)
            else:
                messages.error(request, f"Payment initiation failed: {result.get('error', 'Unknown error')}")
                return redirect('store:order_confirmation', order_id=order.id)
                
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('store:order_confirmation', order_id=order.id)
        except Exception as e:
            print(f"Error initiating M-Pesa payment: {e}")
            import traceback
            traceback.print_exc()
            messages.error(request, "An error occurred while initiating payment. Please try again.")
            return redirect('store:order_confirmation', order_id=order.id)
    
    return redirect('store:order_confirmation', order_id=order.id)

# Receipt and Invoice Views

@login_required
def download_receipt(request, order_id):
    """Download receipt for an order"""
    order = get_object_or_404(Order, id=order_id)
    
    # Security check
    if request.user.is_authenticated:
        if order.user and order.user != request.user:
            messages.error(request, "You don't have permission to download this receipt.")
            return redirect('store:home')
    
    # Get transaction if available
    transaction = order.mpesa_transactions.filter(status='completed').first()
    
    # Generate receipt
    doc_generator = DocumentGenerator()
    pdf_buffer = doc_generator.generate_receipt(order, transaction)
    
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    filename = f"receipt_order_{order.id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
def download_invoice(request, order_id):
    """Download invoice for an order"""
    order = get_object_or_404(Order, id=order_id)
    
    # Security check
    if request.user.is_authenticated:
        if order.user and order.user != request.user:
            messages.error(request, "You don't have permission to download this invoice.")
            return redirect('store:home')
    
    # Generate invoice
    doc_generator = DocumentGenerator()
    pdf_buffer = doc_generator.generate_invoice(order)
    
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    filename = f"invoice_order_{order.id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
def download_booking_receipt(request, booking_id):
    """Download receipt for service booking"""
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    
    # Get transaction if available
    transaction = None
    # Find the related M-Pesa transaction through the dummy order
    from .models import Order
    dummy_orders = Order.objects.filter(
        delivery_instructions__startswith=f'BOOKING_ID:{booking_id}'
    )
    if dummy_orders.exists():
        dummy_order = dummy_orders.first()
        transaction = dummy_order.mpesa_transactions.filter(status='completed').first()
    
    # Generate receipt
    doc_generator = DocumentGenerator()
    pdf_buffer = doc_generator.generate_booking_receipt(booking, transaction)
    
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    filename = f"booking_receipt_{booking_id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


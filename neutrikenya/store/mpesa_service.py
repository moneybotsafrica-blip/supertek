import base64
import datetime
import json
import requests
from django.conf import settings
from .models import MpesaConfiguration, MpesaTransaction, Order, Booking


class MpesaService:
    """Service class for handling M-Pesa Daraja API operations"""
    
    def __init__(self):
        self.config = self._get_active_config()
        if not self.config:
            raise ValueError("No active M-Pesa configuration found")
        
        # Validate required configuration fields
        required_fields = ['consumer_key', 'consumer_secret', 'passkey', 'shortcode', 'callback_url']
        for field in required_fields:
            if not getattr(self.config, field, None):
                raise ValueError(f"M-Pesa configuration missing required field: {field}")
        
        print(f"M-Pesa Service initialized with shortcode: {self.config.shortcode}, environment: {self.config.environment}")
    
    def _get_active_config(self):
        """Get the active M-Pesa configuration"""
        try:
            return MpesaConfiguration.objects.filter(is_active=True).first()
        except MpesaConfiguration.DoesNotExist:
            return None
    
    def _get_api_url(self, endpoint):
        """Get the appropriate API URL based on environment"""
        if self.config.environment == 'sandbox':
            base_url = 'https://sandbox.safaricom.co.ke'
        else:
            base_url = 'https://api.safaricom.co.ke'
        return f"{base_url}{endpoint}"
    
    def _generate_password(self):
        """Generate password for API authentication"""
        # Format: shortcode + passkey + timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{self.config.shortcode}{self.config.passkey}{timestamp}"
        password_bytes = password_str.encode('ascii')
        return base64.b64encode(password_bytes).decode('utf-8'), timestamp
    
    def _get_access_token(self):
        """Get OAuth access token from M-Pesa API"""
        api_url = self._get_api_url('/oauth/v1/generate?grant_type=client_credentials')
        
        # Create auth string
        auth_str = f"{self.config.consumer_key}:{self.config.consumer_secret}"
        auth_bytes = auth_str.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get('access_token')
        except requests.exceptions.RequestException as e:
            print(f"Error getting access token: {e}")
            return None
    
    def initiate_stk_push(self, phone_number, amount, order_id, callback_url=None, is_booking=False):
        """
        Initiate STK Push payment request
        
        Args:
            phone_number: Customer phone number (format: 254XXXXXXXXX)
            amount: Amount to charge
            order_id: Order ID or Booking ID for reference
            callback_url: Optional custom callback URL
            is_booking: True if this is for a service booking, False for regular order
        
        Returns:
            dict: Response from M-Pesa API or error details
        """
        access_token = self._get_access_token()
        if not access_token:
            return {'success': False, 'error': 'Failed to get access token'}
        
        # Generate password and timestamp
        password, timestamp = self._generate_password()
        
        # Format phone number - ensure it's a string first
        phone_number = str(phone_number)
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]
        
        # Ensure phone number is numeric and valid length
        if not phone_number.isdigit() or len(phone_number) != 12:
            raise ValueError(f"Invalid phone number format: {phone_number}. Must be 12 digits starting with 254")
        
        # Generate unique merchant request ID
        reference_type = "BOOKING" if is_booking else "ORDER"
        merchant_request_id = f"MERCH-{reference_type}-{order_id}-{timestamp}"
        
        # Use custom callback URL if provided, otherwise use config default
        if not callback_url:
            callback_url = self.config.callback_url
            if not callback_url:
                # Use default callback URL based on ALLOWED_HOSTS
                from django.conf import settings
                if settings.ALLOWED_HOSTS:
                    # Use the first non-localhost host
                    domain = next((host for host in settings.ALLOWED_HOSTS if host not in ['localhost', '127.0.0.1']), None)
                    if domain:
                        callback_url = f"https://{domain}/mpesa/callback/"
                if not callback_url:
                    raise ValueError("Callback URL is required. Please set it in M-Pesa configuration or provide it as parameter.")
        
        # Validate callback URL - M-Pesa requires publicly accessible URLs
        if 'localhost' in callback_url or '127.0.0.1' in callback_url:
            raise ValueError("Invalid CallBackURL: M-Pesa requires a publicly accessible URL. Localhost/127.0.0.1 URLs are not supported. Please add your public callback URL in M-Pesa configuration.")
        
        # Prepare STK push request
        api_url = self._get_api_url('/mpesa/stkpush/v1/processrequest')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'BusinessShortCode': self.config.shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),
            'PartyA': phone_number,
            'PartyB': self.config.shortcode,
            'PhoneNumber': phone_number,
            'CallBackURL': callback_url,
            'AccountReference': f"{reference_type}-{order_id}",
            'TransactionDesc': f'Payment for {reference_type} {order_id}'
        }
        
        try:
            response = requests.post(api_url, json=payload, headers=headers)
            
            # Log the request and response for debugging
            print(f"M-Pesa STK Push Request:")
            print(f"URL: {api_url}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            
            # Create transaction record
            # For bookings, we need to create a dummy order or modify the approach
            # For now, we'll create a dummy order for bookings to maintain the model relationship
            if is_booking:
                # Create a placeholder order for the transaction
                from decimal import Decimal
                order = Order.objects.create(
                    first_name="Service",
                    last_name="Booking",
                    email="service@booking.com",
                    phone=phone_number,
                    address="Service Address",
                    city="Service City",
                    payment_method='mpesa',
                    status='pending'
                )
                # Store the booking ID in the delivery_instructions for later reference
                order.delivery_instructions = f"BOOKING_ID:{order_id}"
                order.save()
            else:
                order = Order.objects.get(id=order_id)
            
            transaction = MpesaTransaction.objects.create(
                order=order,
                merchant_request_id=merchant_request_id,
                checkout_request_id=data.get('CheckoutRequestID'),
                response_code=data.get('ResponseCode'),
                response_description=data.get('ResponseDescription'),
                customer_message=data.get('CustomerMessage'),
                amount=amount,
                phone_number=phone_number,
                status='pending'
            )
            
            return {
                'success': True,
                'merchant_request_id': merchant_request_id,
                'checkout_request_id': data.get('CheckoutRequestID'),
                'response_code': data.get('ResponseCode'),
                'response_description': data.get('ResponseDescription'),
                'customer_message': data.get('CustomerMessage'),
                'transaction_id': transaction.id
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error initiating STK push: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_callback(self, callback_data):
        """
        Process M-Pesa callback data
        
        Args:
            callback_data: JSON data from M-Pesa callback
        
        Returns:
            dict: Processing result
        """
        try:
            # Extract relevant data from callback
            body = callback_data.get('Body', {})
            stk_callback = body.get('stkCallback', {})
            
            merchant_request_id = stk_callback.get('MerchantRequestID')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc')
            
            # Find the transaction
            try:
                transaction = MpesaTransaction.objects.get(
                    merchant_request_id=merchant_request_id,
                    checkout_request_id=checkout_request_id
                )
            except MpesaTransaction.DoesNotExist:
                return {'success': False, 'error': 'Transaction not found'}
            
            # Update transaction based on result
            transaction.response_code = str(result_code)
            transaction.response_description = result_desc
            
            if result_code == 0:  # Success
                # Extract payment details
                callback_metadata = stk_callback.get('CallbackMetadata', {})
                metadata_items = callback_metadata.get('Item', [])
                
                amount = None
                receipt_number = None
                transaction_date = None
                phone_number = None
                
                for item in metadata_items:
                    name = item.get('Name')
                    value = item.get('Value')
                    
                    if name == 'Amount':
                        amount = value
                    elif name == 'MpesaReceiptNumber':
                        receipt_number = value
                    elif name == 'TransactionDate':
                        # Parse date format: 20240813124530
                        date_str = str(value)
                        transaction_date = datetime.datetime.strptime(date_str, '%Y%m%d%H%M%S')
                    elif name == 'PhoneNumber':
                        phone_number = value
                
                # Update transaction with success details
                transaction.amount = amount
                transaction.receipt_number = receipt_number
                transaction.transaction_date = transaction_date
                transaction.phone_number = phone_number
                transaction.status = 'completed'
                
                # Update order payment status
                order = transaction.order
                order.payment_status = 'completed'
                # Update order status from pending_payment to pending if it was pending_payment
                if order.status == 'pending_payment':
                    order.status = 'pending'
                order.save()
                
                # Check if this is a booking payment
                if order.delivery_instructions and order.delivery_instructions.startswith('BOOKING_ID:'):
                    try:
                        booking_id = int(order.delivery_instructions.split(':')[1])
                        booking = Booking.objects.get(id=booking_id)
                        
                        # Update booking payment status
                        booking.payment_status = 'paid'
                        booking.status = 'assigned'
                        
                        # Auto-assign technician if not already assigned
                        if not booking.technician:
                            available_technicians = Technician.objects.filter(
                                skills=booking.service,
                                is_available=True
                            ).order_by('-rating', '-total_jobs')
                            
                            if available_technicians.exists():
                                booking.technician = available_technicians.first()
                        
                        booking.save()
                        print(f"Booking {booking_id} payment processed successfully")
                        
                    except (Booking.DoesNotExist, ValueError, IndexError) as e:
                        print(f"Error processing booking payment: {e}")
                
            else:  # Failed
                transaction.status = 'failed'
                transaction.customer_message = result_desc
                
                # Update order payment status
                order = transaction.order
                order.payment_status = 'failed'
                # If order was pending_payment, cancel it since payment failed
                if order.status == 'pending_payment':
                    order.status = 'cancelled'
                order.save()
            
            transaction.save()
            
            return {
                'success': True,
                'result_code': result_code,
                'result_desc': result_desc,
                'transaction_id': transaction.id
            }
            
        except Exception as e:
            print(f"Error processing callback: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_transaction_status(self, checkout_request_id):
        """
        Check the status of a transaction using M-Pesa API
        
        Args:
            checkout_request_id: The checkout request ID from STK push
        
        Returns:
            dict: Transaction status
        """
        access_token = self._get_access_token()
        if not access_token:
            return {'success': False, 'error': 'Failed to get access token'}
        
        # Generate password and timestamp
        password, timestamp = self._generate_password()
        
        api_url = self._get_api_url('/mpesa/stkpushquery/v1/query')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'BusinessShortCode': self.config.shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'CheckoutRequestID': checkout_request_id
        }
        
        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            return {
                'success': True,
                'data': data
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error checking transaction status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
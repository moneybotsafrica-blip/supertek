from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from store.models import Technician, Booking, Service, Vehicle, Quotation, Product, Order

class Command(BaseCommand):
    help = 'Set up default permission groups for staff roles'

    def handle(self, *args, **options):
        self.stdout.write('Setting up staff permission groups...')
        
        # Get content types
        technician_ct = ContentType.objects.get_for_model(Technician)
        booking_ct = ContentType.objects.get_for_model(Booking)
        service_ct = ContentType.objects.get_for_model(Service)
        vehicle_ct = ContentType.objects.get_for_model(Vehicle)
        quotation_ct = ContentType.objects.get_for_model(Quotation)
        product_ct = ContentType.objects.get_for_model(Product)
        order_ct = ContentType.objects.get_for_model(Order)
        
        # Create Technician Group
        tech_group, created = Group.objects.get_or_create(name='Technicians')
        if created:
            self.stdout.write('Created Technicians group')
        
        # Add technician-specific permissions
        tech_permissions = [
            # View permissions
            Permission.objects.get(codename='view_technician', content_type=technician_ct),
            Permission.objects.get(codename='view_booking', content_type=booking_ct),
            Permission.objects.get(codename='view_service', content_type=service_ct),
            Permission.objects.get(codename='view_vehicle', content_type=vehicle_ct),
            Permission.objects.get(codename='view_quotation', content_type=quotation_ct),
            # Custom permissions
            Permission.objects.get(codename='view_technician_dashboard', content_type=technician_ct),
            Permission.objects.get(codename='manage_own_bookings', content_type=technician_ct),
            Permission.objects.get(codename='create_quotations', content_type=technician_ct),
            Permission.objects.get(codename='manage_vehicles', content_type=technician_ct),
            Permission.objects.get(codename='view_sales_reports', content_type=technician_ct),
            Permission.objects.get(codename='manage_clock_in_out', content_type=technician_ct),
        ]
        
        tech_group.permissions.set(tech_permissions)
        self.stdout.write(f'Added {len(tech_permissions)} permissions to Technicians group')
        
        # Create Sales Staff Group
        sales_group, created = Group.objects.get_or_create(name='Sales Staff')
        if created:
            self.stdout.write('Created Sales Staff group')
        
        # Add sales-specific permissions
        sales_permissions = [
            # View permissions
            Permission.objects.get(codename='view_product', content_type=product_ct),
            Permission.objects.get(codename='view_order', content_type=order_ct),
            Permission.objects.get(codename='view_booking', content_type=booking_ct),
            Permission.objects.get(codename='view_quotation', content_type=quotation_ct),
        ]
        
        sales_group.permissions.set(sales_permissions)
        self.stdout.write(f'Added {len(sales_permissions)} permissions to Sales Staff group')
        
        # Create Admin Staff Group
        admin_group, created = Group.objects.get_or_create(name='Admin Staff')
        if created:
            self.stdout.write('Created Admin Staff group')
        
        # Add admin-specific permissions (full access to their areas)
        admin_permissions = Permission.objects.filter(
            content_type__in=[technician_ct, booking_ct, service_ct, vehicle_ct, quotation_ct]
        )
        
        admin_group.permissions.set(admin_permissions)
        self.stdout.write(f'Added {len(admin_permissions)} permissions to Admin Staff group')
        
        self.stdout.write(self.style.SUCCESS('Successfully set up staff permission groups!'))
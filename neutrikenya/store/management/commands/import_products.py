import os
import re
import shutil
from django.core.management.base import BaseCommand
from django.core.files import File
from django.utils.text import slugify
from store.models import Category, Product, ProductImage

class Command(BaseCommand):
    help = 'Import products from outdoor camping products zip extraction'

    def handle(self, *args, **options):
        source_path = r"C:\Users\Moneybots\Downloads\neutrikenya\temp_extract\outdoor_camping_products"
        media_products_path = r"C:\Users\Moneybots\Downloads\neutrikenya\neutrikenya\media\products"
        
        # Category mapping function
        def get_category(product_name):
            lower_name = product_name.lower()
            
            if any(keyword in lower_name for keyword in ['phone', 'doogee', 'smartphone']):
                return Category.objects.get(slug='rugged-phones')
            elif any(keyword in lower_name for keyword in ['tablet', 'getac', 'keyboard', 'dock']):
                return Category.objects.get(slug='tablets-accessories')
            elif any(keyword in lower_name for keyword in ['scanner', 'datalogic', 'barcode', 'mobile computer']):
                return Category.objects.get(slug='scanners-mobile-computers')
            elif any(keyword in lower_name for keyword in ['honeywell', 'mobility', 'ck71', 'ck75']):
                return Category.objects.get(slug='mobility-equipment')
            elif any(keyword in lower_name for keyword in ['posiflex', 'pos']):
                return Category.objects.get(slug='pos-systems')
            elif any(keyword in lower_name for keyword in ['fridge', 'freezer', 'national luna', 'snomaster', 'nl']):
                return Category.objects.get(slug='portable-fridges-freezers')
            elif any(keyword in lower_name for keyword in ['braai', 'bbq', 'megamaster', 'sierra', 'kamado']):
                return Category.objects.get(slug='bbq-grilling')
            elif any(keyword in lower_name for keyword in ['printer', 'epson', 'workforce', 'toner', 'ink']):
                return Category.objects.get(slug='printers-office-equipment')
            elif any(keyword in lower_name for keyword in ['projector', 'eb-']):
                return Category.objects.get(slug='projectors')
            elif any(keyword in lower_name for keyword in ['videofied', 'motionviewer', 'keypad']):
                return Category.objects.get(slug='security-systems')
            elif any(keyword in lower_name for keyword in ['heater', 'alva', 'patio heater']):
                return Category.objects.get(slug='heaters')
            elif any(keyword in lower_name for keyword in ['campmor', 'tent', 'mosquito', 'camping', 'portable', 'fold']):
                return Category.objects.get(slug='camping-equipment')
            elif any(keyword in lower_name for keyword in ['ice maker', 'ice-maker']):
                return Category.objects.get(slug='ice-makers')
            elif any(keyword in lower_name for keyword in ['coffee', 'gaggia', 'ristora', 'tea']):
                return Category.objects.get(slug='coffee-beverages')
            elif any(keyword in lower_name for keyword in ['food', 'bakali', 'corn bites', 'chips']):
                return Category.objects.get(slug='food-snacks')
            elif any(keyword in lower_name for keyword in ['battery', 'charger', 'power']):
                return Category.objects.get(slug='power-accessories')
            elif any(keyword in lower_name for keyword in ['cable', 'plug', 'coupler', 'tow']):
                return Category.objects.get(slug='accessories')
            else:
                return Category.objects.get(slug='other')

        # Ensure media products directory exists
        os.makedirs(media_products_path, exist_ok=True)
        
        # Process each product folder
        products_created = 0
        products_updated = 0
        errors = []
        
        for folder_name in sorted(os.listdir(source_path)):
            folder_path = os.path.join(source_path, folder_name)
            if not os.path.isdir(folder_path):
                continue
            
            try:
                # Read product details
                details_file = os.path.join(folder_path, "product_details.txt")
                description_file = os.path.join(folder_path, "description.txt")
                
                if not os.path.exists(details_file):
                    self.stdout.write(self.style.WARNING(f'Skipping {folder_name}: No product_details.txt'))
                    continue
                
                with open(details_file, 'r', encoding='utf-8', errors='ignore') as f:
                    details_content = f.read()
                
                # Parse product details
                product_id_match = re.search(r'Product ID: (\d+)', details_content)
                name_match = re.search(r'Name: (.+)', details_content)
                price_match = re.search(r'Price: ([\d.]+)', details_content)
                regular_price_match = re.search(r'Regular Price: ([\d.]+)', details_content)
                
                if not name_match:
                    self.stdout.write(self.style.WARNING(f'Skipping {folder_name}: No product name'))
                    continue
                
                product_name = name_match.group(1).strip()
                product_slug = slugify(product_name)
                
                # Parse prices
                price = 0
                original_price = None
                
                if price_match:
                    try:
                        price = float(price_match.group(1))
                    except ValueError:
                        price = 0
                
                if regular_price_match:
                    try:
                        original_price = float(regular_price_match.group(1))
                    except ValueError:
                        original_price = None
                
                # Read description
                description = ""
                if os.path.exists(description_file):
                    with open(description_file, 'r', encoding='utf-8', errors='ignore') as f:
                        description = f.read().strip()
                
                # Get category
                try:
                    category = get_category(product_name)
                except Category.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'No category found for {product_name}, using "Other"'))
                    category = Category.objects.get(slug='other')
                
                # Create or update product
                product, created = Product.objects.get_or_create(
                    slug=product_slug,
                    defaults={
                        'name': product_name,
                        'description': description,
                        'price': price,
                        'original_price': original_price,
                        'category': category,
                        'is_available': True,
                        'stock': 10,  # Default stock
                    }
                )
                
                if created:
                    products_created += 1
                    self.stdout.write(self.style.SUCCESS(f'Created product: {product_name}'))
                else:
                    # Update existing product
                    product.name = product_name
                    product.description = description
                    product.price = price
                    product.original_price = original_price
                    product.category = category
                    product.save()
                    products_updated += 1
                    self.stdout.write(self.style.WARNING(f'Updated product: {product_name}'))
                
                # Process images
                image_files = []
                for file_name in os.listdir(folder_path):
                    if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                        image_files.append(file_name)
                
                # Sort image files to ensure consistent ordering
                image_files.sort()
                
                # Remove existing images if updating
                if not created:
                    product.images.all().delete()
                
                # Copy and add images
                for idx, image_file in enumerate(image_files):
                    source_image = os.path.join(folder_path, image_file)
                    
                    # Create a unique filename for the destination
                    file_ext = os.path.splitext(image_file)[1]
                    dest_filename = f"{product_slug}_{idx}{file_ext}"
                    dest_image = os.path.join(media_products_path, dest_filename)
                    
                    # Copy image file
                    shutil.copy2(source_image, dest_image)
                    
                    # Create ProductImage record
                    with open(dest_image, 'rb') as f:
                        product_image = ProductImage(
                            product=product,
                            image=File(f, name=dest_filename),
                            is_main=(idx == 0)  # First image is main
                        )
                        product_image.save()
                
                if image_files:
                    self.stdout.write(f'  Added {len(image_files)} images')
                
            except Exception as e:
                error_msg = f"Error processing {folder_name}: {str(e)}"
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(error_msg))
        
        # Print summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nImport Summary:\n'
                f'Products created: {products_created}\n'
                f'Products updated: {products_updated}\n'
                f'Total products processed: {products_created + products_updated}'
            )
        )
        
        if errors:
            self.stdout.write(
                self.style.ERROR(
                    f'\nErrors encountered: {len(errors)}\n'
                    f'First 10 errors:\n' + '\n'.join(errors[:10])
                )
            )
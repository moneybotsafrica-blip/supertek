from django.core.management.base import BaseCommand
from store.models import Product, Category, ProductImage

class Command(BaseCommand):
    help = 'Verify product import and show statistics'

    def handle(self, *args, **options):
        # Count products by category
        self.stdout.write('Product Import Verification:')
        self.stdout.write('=' * 50)
        
        categories = Category.objects.all()
        total_products = 0
        total_images = ProductImage.objects.count()
        
        for category in categories:
            product_count = Product.objects.filter(category=category).count()
            if product_count > 0:
                self.stdout.write('\n{}: {} products'.format(category.name, product_count))
                
                # Show sample products
                sample_products = Product.objects.filter(category=category)[:3]
                for product in sample_products:
                    image_count = product.images.count()
                    self.stdout.write('  - {} ({} images)'.format(product.name, image_count))
                
                total_products += product_count
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('Total Categories: {}'.format(categories.count()))
        self.stdout.write('Total Products: {}'.format(total_products))
        self.stdout.write('Total Product Images: {}'.format(total_images))
        avg_images = total_images / total_products if total_products > 0 else 0
        self.stdout.write('Average Images per Product: {:.2f}'.format(avg_images))

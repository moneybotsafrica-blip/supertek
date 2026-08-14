from django.core.management.base import BaseCommand
from store.models import Product, Category, ProductImage

class Command(BaseCommand):
    help = 'Remove all products and clear database'

    def handle(self, *args, **options):
        # Count products before deletion
        product_count = Product.objects.count()
        category_count = Category.objects.count()
        image_count = ProductImage.objects.count()
        
        self.stdout.write('Before cleanup:')
        self.stdout.write('  Products: {}'.format(product_count))
        self.stdout.write('  Categories: {}'.format(category_count))
        self.stdout.write('  Product Images: {}'.format(image_count))
        
        # Delete all product images
        ProductImage.objects.all().delete()
        
        # Delete all products
        Product.objects.all().delete()
        
        # Delete all categories
        Category.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('Successfully cleaned up all products, categories, and images'))

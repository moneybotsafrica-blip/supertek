from django.core.management.base import BaseCommand
from store.models import Category

class Command(BaseCommand):
    help = 'Import outdoor and camping product categories'

    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Accessories',
                'slug': 'accessories',
                'description': 'Various accessories including cables, plugs, couplers, and towing equipment'
            },
            {
                'name': 'BBQ & Grilling',
                'slug': 'bbq-grilling',
                'description': 'Gas and charcoal braais, BBQ grills, and outdoor cooking equipment'
            },
            {
                'name': 'Camping Equipment',
                'slug': 'camping-equipment',
                'description': 'Tents, mosquito nets, portable furniture, and camping essentials'
            },
            {
                'name': 'Coffee & Beverages',
                'slug': 'coffee-beverages',
                'description': 'Coffee machines, instant coffee, tea, and beverage supplies'
            },
            {
                'name': 'Food & Snacks',
                'slug': 'food-snacks',
                'description': 'Snacks, corn bites, lentil chips, and food products'
            },
            {
                'name': 'Heaters',
                'slug': 'heaters',
                'description': 'Patio heaters, gas heaters, and indoor heating solutions'
            },
            {
                'name': 'Ice Makers',
                'slug': 'ice-makers',
                'description': 'Portable and commercial ice making machines'
            },
            {
                'name': 'Mobility Equipment',
                'slug': 'mobility-equipment',
                'description': 'Honeywell mobility equipment, handheld computers, and industrial devices'
            },
            {
                'name': 'Other',
                'slug': 'other',
                'description': 'Miscellaneous products and equipment'
            },
            {
                'name': 'POS Systems',
                'slug': 'pos-systems',
                'description': 'Point of sale systems, POS terminals, and related equipment'
            },
            {
                'name': 'Portable Fridges & Freezers',
                'slug': 'portable-fridges-freezers',
                'description': 'Portable refrigerators, freezers, and cooling equipment for outdoor use'
            },
            {
                'name': 'Power & Accessories',
                'slug': 'power-accessories',
                'description': 'Battery chargers, power inverters, and power accessories'
            },
            {
                'name': 'Printers & Office Equipment',
                'slug': 'printers-office-equipment',
                'description': 'Printers, scanners, toner cartridges, and office equipment'
            },
            {
                'name': 'Projectors',
                'slug': 'projectors',
                'description': 'Epson projectors and projection equipment'
            },
            {
                'name': 'Rugged Phones',
                'slug': 'rugged-phones',
                'description': 'DOOGEE rugged smartphones and durable mobile devices'
            },
            {
                'name': 'Scanners & Mobile Computers',
                'slug': 'scanners-mobile-computers',
                'description': 'Barcode scanners, mobile computers, and data collection devices'
            },
            {
                'name': 'Security Systems',
                'slug': 'security-systems',
                'description': 'Videofied security systems, motion viewers, and security equipment'
            },
            {
                'name': 'Tablets & Accessories',
                'slug': 'tablets-accessories',
                'description': 'GETAC rugged tablets, keyboard docks, and tablet accessories'
            },
        ]

        created_count = 0
        updated_count = 0

        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            else:
                # Update existing category
                category.name = cat_data['name']
                category.description = cat_data['description']
                category.save()
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated category: {category.name}'))

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {created_count} categories created, {updated_count} categories updated'
            )
        )
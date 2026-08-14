from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
import os
from store.models import Advertisement, Banner, Video

class Command(BaseCommand):
    help = 'Import existing images and videos from templates into admin content models'

    def handle(self, *args, **options):
        self.stdout.write('Importing existing content...')
        
        static_root = settings.BASE_DIR / 'static' / 'images'
        
        # Import Advertisements
        advertisements = [
            ('WhatsApp Advertisement', 'whatsapp-advert-1.jpeg', 1),
            ('BBQ Advertisement 1', 'bbq-advert-1.jpg', 2),
            ('BBQ Advertisement 2', 'bbq-advert-2.jpg', 3),
            ('BBQ Advertisement 3', 'bbq-advert-3.jpg', 4),
            ('Vehicle Drawers Advertisement', 'vehicle-drawers-advert.jpeg', 5),
            ('Car Fridge Advertisement', 'car-fridge-advert.jpeg', 6),
            ('Gas Cooker Advertisement', 'gas-cooker-advert.jpeg', 7),
        ]
        
        for title, filename, order in advertisements:
            if not Advertisement.objects.filter(title=title).exists():
                image_path = static_root / filename
                if image_path.exists():
                    with open(image_path, 'rb') as f:
                        advertisement = Advertisement.objects.create(
                            title=title,
                            display_order=order,
                            is_active=True
                        )
                        advertisement.image.save(filename, File(f), save=True)
                    self.stdout.write(f'Created advertisement: {title}')
                else:
                    self.stdout.write(f'Image not found: {filename}')
            else:
                self.stdout.write(f'Advertisement already exists: {title}')
        
        # Import Hero Banners
        hero_banners = [
            ('Camping Gear Hero', 'camping-gear.jpg', 'hero', 1),
            ('BBQ Equipment Hero', 'bbq.jpg', 'hero', 2),
            ('Portable Fridges Hero', 'fridge.jpg', 'hero', 3),
            ('Camping Essentials Hero', 'camping-gear.jpg', 'hero', 4),
            ('Camping Adventure Hero', 'camping-hero-right-1.jpeg', 'hero', 5),
            ('Outdoor Experience Hero', 'camping-hero-right-2.jpeg', 'hero', 6),
        ]
        
        for title, filename, banner_type, order in hero_banners:
            if not Banner.objects.filter(title=title).exists():
                image_path = static_root / filename
                if image_path.exists():
                    with open(image_path, 'rb') as f:
                        banner = Banner.objects.create(
                            title=title,
                            banner_type=banner_type,
                            display_order=order,
                            is_active=True
                        )
                        banner.image.save(filename, File(f), save=True)
                    self.stdout.write(f'Created banner: {title}')
                else:
                    self.stdout.write(f'Image not found: {filename}')
            else:
                self.stdout.write(f'Banner already exists: {title}')
        
        # Import Video
        video_filename = 'outdoor.mp4'
        if not Video.objects.filter(title='Outdoor Video').exists():
            video_path = static_root / video_filename
            if video_path.exists():
                with open(video_path, 'rb') as f:
                    video = Video.objects.create(
                        title='Outdoor Video',
                        section='hero',
                        description='Outdoor equipment showcase video',
                        display_order=1,
                        is_active=True
                    )
                    video.video_file.save(video_filename, File(f), save=True)
                self.stdout.write(f'Created video: Outdoor Video')
            else:
                self.stdout.write(f'Video not found: {video_filename}')
        else:
            self.stdout.write('Video already exists: Outdoor Video')
        
        self.stdout.write(self.style.SUCCESS('Successfully imported existing content!'))

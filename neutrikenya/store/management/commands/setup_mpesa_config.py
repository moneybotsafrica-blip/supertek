from django.core.management.base import BaseCommand
from store.models import MpesaConfiguration

class Command(BaseCommand):
    help = 'Setup M-Pesa configuration with credentials'

    def add_arguments(self, parser):
        parser.add_argument('--consumer_key', type=str, help='M-Pesa Consumer Key')
        parser.add_argument('--consumer_secret', type=str, help='M-Pesa Consumer Secret')
        parser.add_argument('--passkey', type=str, help='M-Pesa Passkey (for STK push)')
        parser.add_argument('--shortcode', type=str, help='M-Pesa Business Short Code')
        parser.add_argument('--environment', type=str, default='sandbox', help='Environment (sandbox/production)')
        parser.add_argument('--callback_url', type=str, help='Callback URL for M-Pesa responses')

    def handle(self, *args, **options):
        consumer_key = options.get('consumer_key')
        consumer_secret = options.get('consumer_secret')
        passkey = options.get('passkey')
        shortcode = options.get('shortcode')
        environment = options.get('environment')
        callback_url = options.get('callback_url')

        # Deactivate existing configurations
        MpesaConfiguration.objects.all().update(is_active=False)

        # Create new configuration
        config = MpesaConfiguration.objects.create(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            passkey=passkey,
            shortcode=shortcode,
            environment=environment,
            callback_url=callback_url,
            is_active=True
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully created M-Pesa configuration: {config}'))
        self.stdout.write(f'Environment: {config.environment}')
        self.stdout.write(f'Shortcode: {config.shortcode}')
        self.stdout.write(f'Callback URL: {config.callback_url or "Not set"}')
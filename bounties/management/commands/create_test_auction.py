from django.core.management.base import BaseCommand
from bounties.auction_models import Auction
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create a test auction for frontend testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--title',
            type=str,
            default='5-DAY MEAL PASS @ ST RINA',
            help='Title of the auction'
        )
        parser.add_argument(
            '--description', 
            type=str,
            default='Test auction for frontend integration - 5-Day Meal Pass at ST Rina Restaurant',
            help='Description of the auction'
        )
        parser.add_argument(
            '--minimum-bid',
            type=int,
            default=1000,
            help='Minimum starting bid amount'
        )
        parser.add_argument(
            '--duration-hours',
            type=int,
            default=24,
            help='Duration of auction in hours'
        )

    def handle(self, *args, **options):
        # Check if there's already an active auction
        active_auction = Auction.objects.filter(status='active').first()
        if active_auction:
            self.stdout.write(
                self.style.WARNING(f'Active auction already exists: {active_auction.title}')
            )
            return

        # Check if there's a pending auction
        pending_auction = Auction.objects.filter(status='pending').first()
        if pending_auction:
            self.stdout.write(
                self.style.WARNING(f'Pending auction already exists: {pending_auction.title}')
            )
            return

        # Create test auction
        now = timezone.now()
        starts_at = now
        ends_at = now + timedelta(hours=options['duration_hours'])

        auction = Auction.objects.create(
            title=options['title'],
            description=options['description'],
            minimum_bid=options['minimum_bid'],
            starts_at=starts_at,
            ends_at=ends_at,
            status='active'
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created test auction: "{auction.title}"\n'
                f'ID: {auction.id}\n'
                f'Status: {auction.status}\n'
                f'Starts: {auction.starts_at}\n'
                f'Ends: {auction.ends_at}\n'
                f'Minimum Bid: {auction.minimum_bid} coins'
            )
        )
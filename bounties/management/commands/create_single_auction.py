from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from bounties.auction_models import Auction
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create or update the single active auction'

    def add_arguments(self, parser):
        parser.add_argument(
            '--title',
            type=str,
            help='Title of the auction',
            default='iPhone 15 Pro'
        )
        parser.add_argument(
            '--description',
            type=str,
            help='Description of the auction',
            default='Latest iPhone model with all features'
        )
        parser.add_argument(
            '--minimum-bid',
            type=int,
            help='Minimum starting bid in coins',
            default=1000
        )
        parser.add_argument(
            '--starts-in',
            type=int,
            help='Hours until auction starts (0 for immediate)',
            default=0
        )
        parser.add_argument(
            '--duration',
            type=int,
            help='Auction duration in hours',
            default=24
        )
        parser.add_argument(
            '--admin-username',
            type=str,
            help='Username of the admin creating the auction',
            default='delo'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force create/update even if another auction exists'
        )

    def handle(self, *args, **options):
        title = options['title']
        description = options['description']
        minimum_bid = options['minimum_bid']
        starts_in = options['starts_in']
        duration = options['duration']
        admin_username = options['admin_username']
        force = options['force']

        # Find admin user
        try:
            admin_user = User.objects.get(username=admin_username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Admin user "{admin_username}" not found')
            )
            return

        # Check if there's already an active auction
        active_auction = Auction.objects.filter(status='active').first()
        pending_auction = Auction.objects.filter(status='pending').first()

        if active_auction and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'Active auction already exists: "{active_auction.title}" '
                    f'(ID: {active_auction.id}). Use --force to override.'
                )
            )
            return

        if pending_auction and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'Pending auction already exists: "{pending_auction.title}" '
                    f'(ID: {pending_auction.id}). Use --force to override.'
                )
            )
            return

        # Calculate timing
        now = timezone.now()
        starts_at = now + timedelta(hours=starts_in)
        ends_at = starts_at + timedelta(hours=duration)

        # Determine status
        if starts_in == 0:
            status = 'active'
        else:
            status = 'pending'

        # Create or update auction
        if pending_auction and force:
            # Update existing pending auction
            pending_auction.title = title
            pending_auction.description = description
            pending_auction.minimum_bid = minimum_bid
            pending_auction.starts_at = starts_at
            pending_auction.ends_at = ends_at
            pending_auction.status = status
            pending_auction.created_by = admin_user
            pending_auction.save()
            auction = pending_auction
            action = "Updated"
        elif active_auction and force:
            # Update existing active auction
            active_auction.title = title
            active_auction.description = description
            active_auction.minimum_bid = minimum_bid
            active_auction.starts_at = starts_at
            active_auction.ends_at = ends_at
            active_auction.status = status
            active_auction.created_by = admin_user
            active_auction.save()
            auction = active_auction
            action = "Updated"
        else:
            # Create new auction
            auction = Auction.objects.create(
                title=title,
                description=description,
                minimum_bid=minimum_bid,
                starts_at=starts_at,
                ends_at=ends_at,
                status=status,
                created_by=admin_user
            )
            action = "Created"

        # Output results
        self.stdout.write(
            self.style.SUCCESS(
                f'{action} auction successfully!'
            )
        )
        self.stdout.write(f'  Title: {auction.title}')
        self.stdout.write(f'  Description: {auction.description}')
        self.stdout.write(f'  Minimum Bid: {auction.minimum_bid} coins')
        self.stdout.write(f'  Status: {auction.status}')
        self.stdout.write(f'  Starts At: {auction.starts_at.strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write(f'  Ends At: {auction.ends_at.strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write(f'  Created By: {auction.created_by.username}')
        self.stdout.write(f'  Auction ID: {auction.id}')

        if auction.status == 'pending':
            self.stdout.write(
                self.style.WARNING(
                    f'Auction will start in {starts_in} hours. '
                    f'To make it active immediately, use --starts-in=0'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'You can now manage this auction in Django admin at: '
                f'http://127.0.0.1:8000/admin/bounties/auction/{auction.id}/change/'
            )
        )
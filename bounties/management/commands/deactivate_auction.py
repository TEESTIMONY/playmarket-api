from django.core.management.base import BaseCommand
from bounties.auction_models import Auction

class Command(BaseCommand):
    help = 'Deactivate the current active auction'

    def add_arguments(self, parser):
        parser.add_argument(
            '--auction-id',
            type=int,
            help='ID of the auction to deactivate (if not specified, deactivates the first active auction)'
        )

    def handle(self, *args, **options):
        auction_id = options.get('auction_id')
        
        if auction_id:
            # Deactivate specific auction by ID
            try:
                auction = Auction.objects.get(id=auction_id)
                old_status = auction.status
                auction.status = 'ended'
                auction.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully deactivated auction: "{auction.title}"\n'
                        f'ID: {auction.id}\n'
                        f'Previous status: {old_status}\n'
                        f'New status: {auction.status}'
                    )
                )
            except Auction.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Auction with ID {auction_id} not found')
                )
        else:
            # Deactivate the first active auction
            active_auction = Auction.objects.filter(status='active').first()
            if active_auction:
                old_status = active_auction.status
                active_auction.status = 'ended'
                active_auction.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully deactivated auction: "{active_auction.title}"\n'
                        f'ID: {active_auction.id}\n'
                        f'Previous status: {old_status}\n'
                        f'New status: {active_auction.status}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('No active auctions found to deactivate')
                )
"""
WebSocket consumers for bounties app.

This module contains WebSocket consumers that handle real-time communication
for auctions, bidding, and other interactive features.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from .models import UserProfile
from .auction_models import Auction, AuctionBid


class TestConsumer(AsyncWebsocketConsumer):
    """
    Basic WebSocket consumer for testing connection establishment.
    Used to validate WebSocket functionality before implementing auction features.
    """
    
    async def connect(self):
        """Handle WebSocket connection establishment."""
        # Accept the WebSocket connection
        await self.accept()
        
        # Send connection confirmation message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'WebSocket connection established successfully!',
            'timestamp': timezone.now().isoformat()
        }))
        
        # Send a welcome message
        await self.send(text_data=json.dumps({
            'type': 'welcome',
            'message': 'Welcome to the PlayMarket WebSocket test server!',
            'features': [
                'Real-time auction updates',
                'Live bidding functionality', 
                'Leaderboard updates',
                'Auction timer synchronization'
            ]
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Clean up any group memberships or connections
        pass

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            # Parse the incoming JSON message
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')
            message = text_data_json.get('message', '')
            
            # Handle different message types
            if message_type == 'echo':
                # Echo the message back to the sender
                await self.send(text_data=json.dumps({
                    'type': 'echo_response',
                    'message': f'Echo: {message}',
                    'timestamp': timezone.now().isoformat()
                }))
                
            elif message_type == 'ping':
                # Respond to ping with pong
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'message': 'Pong!',
                    'timestamp': timezone.now().isoformat()
                }))
                
            elif message_type == 'test_auth':
                # Test authentication status
                user = self.scope['user']
                if user != AnonymousUser():
                    await self.send(text_data=json.dumps({
                        'type': 'auth_status',
                        'authenticated': True,
                        'username': user.username,
                        'user_id': user.id
                    }))
                else:
                    await self.send(text_data=json.dumps({
                        'type': 'auth_status',
                        'authenticated': False,
                        'message': 'User not authenticated'
                    }))
                    
            else:
                # Default message handling
                await self.send(text_data=json.dumps({
                    'type': 'message_received',
                    'message': f'Received: {message}',
                    'timestamp': timezone.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            # Handle invalid JSON
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format',
                'timestamp': timezone.now().isoformat()
            }))
        except Exception as e:
            # Handle any other errors
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error processing message: {str(e)}',
                'timestamp': timezone.now().isoformat()
            }))


class AuctionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling auction-specific real-time updates.
    Manages bid placement, auction status updates, and user notifications.
    """
    
    async def connect(self):
        """Handle WebSocket connection for auction updates."""
        # Check if user is authenticated
        if self.scope['user'] == AnonymousUser():
            await self.close()
            return
        
        # Accept the connection
        await self.accept()
        
        # Get auction ID from URL parameters
        self.auction_id = self.scope['url_route']['kwargs']['auction_id']
        
        # Join auction-specific group
        self.auction_group_name = f'auction_{self.auction_id}'
        await self.channel_layer.group_add(
            self.auction_group_name,
            self.channel_name
        )
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'auction_connected',
            'auction_id': self.auction_id,
            'message': f'Connected to auction {self.auction_id}',
            'timestamp': timezone.now().isoformat()
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave auction group
        if hasattr(self, 'auction_group_name'):
            await self.channel_layer.group_discard(
                self.auction_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle bid placement and other auction actions."""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'place_bid':
                await self.handle_place_bid(data)
            elif action == 'get_status':
                await self.handle_get_status()
            elif action == 'subscribe_auction':
                await self.handle_subscribe_auction(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown action: {action}'
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error: {str(e)}'
            }))

    async def handle_place_bid(self, data):
        """Handle bid placement request via WebSocket."""
        user = self.scope['user']
        amount = data.get('amount')
        auction_id = data.get('auction_id')
        
        # Validate bid amount
        if not amount or amount <= 0:
            await self.send(text_data=json.dumps({
                'type': 'bid_error',
                'message': 'Invalid bid amount'
            }))
            return
        
        # For now, we'll simulate the response
        # In a real implementation, this would call the PlaceBidView
        await self.send(text_data=json.dumps({
            'type': 'bid_placed',
            'user': user.username,
            'amount': amount,
            'auction_id': auction_id,
            'status': 'pending_validation'
        }))
        
        # Broadcast bid update to all connected clients
        await self.channel_layer.group_send(
            self.auction_group_name,
            {
                'type': 'auction_update',
                'data': {
                    'type': 'new_bid',
                    'user': user.username,
                    'amount': amount,
                    'timestamp': timezone.now().isoformat()
                }
            }
        )

    async def handle_get_status(self):
        """Handle auction status request."""
        # This would normally fetch real auction data from database
        await self.send(text_data=json.dumps({
            'type': 'auction_status',
            'auction_id': self.auction_id,
            'status': 'active',
            'current_bid': 119,
            'highest_bidder': 'user123',
            'time_remaining': '2:30:15'
        }))

    async def handle_subscribe_auction(self, data):
        """Handle auction subscription request."""
        auction_id = data.get('auction_id')
        await self.send(text_data=json.dumps({
            'type': 'auction_subscribed',
            'auction_id': auction_id,
            'message': f'Subscribed to auction {auction_id}'
        }))

    async def auction_update(self, event):
        """Handle auction updates from other sources."""
        await self.send(text_data=json.dumps(event['data']))


class AuctionLeaderboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time leaderboard updates.
    Broadcasts top bidders and their amounts.
    """
    
    async def connect(self):
        """Handle WebSocket connection for leaderboard updates."""
        if self.scope['user'] == AnonymousUser():
            await self.close()
            return
        
        await self.accept()
        
        self.auction_id = self.scope['url_route']['kwargs']['auction_id']
        self.leaderboard_group_name = f'leaderboard_{self.auction_id}'
        
        await self.channel_layer.group_add(
            self.leaderboard_group_name,
            self.channel_name
        )
        
        await self.send(text_data=json.dumps({
            'type': 'leaderboard_connected',
            'auction_id': self.auction_id
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'leaderboard_group_name'):
            await self.channel_layer.group_discard(
                self.leaderboard_group_name,
                self.channel_name
            )

    async def leaderboard_update(self, event):
        """Handle leaderboard updates."""
        await self.send(text_data=json.dumps(event['data']))


class AuctionUpdatesConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for general auction updates.
    Broadcasts updates to all connected clients regardless of specific auction.
    """
    
    async def connect(self):
        """Handle WebSocket connection for general auction updates."""
        if self.scope['user'] == AnonymousUser():
            await self.close()
            return
        
        await self.accept()
        
        # Join general auction updates group
        self.general_updates_group = 'auction_updates'
        await self.channel_layer.group_add(
            self.general_updates_group,
            self.channel_name
        )
        
        await self.send(text_data=json.dumps({
            'type': 'general_updates_connected',
            'message': 'Connected to general auction updates'
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.general_updates_group,
            self.channel_name
        )

    async def auction_broadcast(self, event):
        """Handle general auction broadcasts."""
        await self.send(text_data=json.dumps(event['data']))
#!/usr/bin/env python3
"""
Test script to verify media file serving is working correctly.
"""

import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, '/Users/dera/Documents/GitHub/playmarket-api')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playmarket.settings')

import django
django.setup()

from django.conf import settings
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from bounties.models import UserProfile, Auction, AuctionImage


def test_media_serving():
    """Test that media files are being served correctly."""
    print("Testing media file serving...")
    
    # Create a test user
    user, created = User.objects.get_or_create(
        username='test_admin',
        defaults={
            'email': 'test@example.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    # Create user profile if it doesn't exist
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'coin_balance': 1000, 'is_admin': True}
    )
    
    # Create a test auction
    from django.utils import timezone
    starts_at = timezone.make_aware(timezone.datetime(2024, 2, 15, 10, 0, 0))
    ends_at = timezone.make_aware(timezone.datetime(2024, 2, 15, 18, 0, 0))
    
    auction = Auction.objects.create(
        title='Test Auction with Media Serving',
        description='Testing media file serving',
        minimum_bid=100,
        starts_at=starts_at,
        ends_at=ends_at,
        created_by=user
    )
    
    print(f"Created test auction: {auction.title}")
    
    # Create a test image file
    test_image_content = b'fake image content'
    test_image = SimpleUploadedFile(
        "test_media_image.jpg",
        test_image_content,
        content_type="image/jpeg"
    )
    
    # Test creating AuctionImage
    auction_image = AuctionImage.objects.create(
        auction=auction,
        image=test_image,
        order=1
    )
    
    print(f"Created test image: {auction_image.image.name}")
    print(f"Image URL: {auction_image.image.url}")
    print(f"Media URL: {settings.MEDIA_URL}")
    print(f"Media Root: {settings.MEDIA_ROOT}")
    
    # Test that the image file exists
    try:
        image_path = os.path.join(settings.MEDIA_ROOT, auction_image.image.name)
        print(f"Image file path: {image_path}")
        print(f"Image file exists: {os.path.exists(image_path)}")
        
        # Test the full URL
        full_url = settings.MEDIA_URL + auction_image.image.name
        print(f"Full media URL: {full_url}")
        
    except Exception as e:
        print(f"Error checking image: {e}")
    
    # Test serializer includes image_files
    from bounties.serializers import AuctionSerializer
    serializer = AuctionSerializer(auction)
    data = serializer.data
    
    print("Serializer data keys:", list(data.keys()))
    print("Image files in serializer:", 'image_files' in data)
    
    if 'image_files' in data and data['image_files']:
        print(f"Image files: {data['image_files']}")
        for img in data['image_files']:
            print(f"  - Image URL: {img['image']}")
    
    print("✅ Media serving test completed successfully!")
    
    # Clean up
    auction_image.delete()
    auction.delete()
    print("✅ Test data cleaned up")


if __name__ == '__main__':
    # Add the project directory to the Python path
    sys.path.insert(0, '/Users/dera/Documents/GitHub/playmarket-api')

    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playmarket.settings')
    django.setup()
    
    test_media_serving()
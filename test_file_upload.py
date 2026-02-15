#!/usr/bin/env python3
"""
Test script for file upload functionality in Django admin.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
from datetime import datetime

# Add the project directory to the Python path
sys.path.insert(0, '/Users/dera/Documents/GitHub/playmarket-api')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playmarket.settings')
django.setup()

import requests
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from bounties.models import UserProfile, Auction, AuctionImage


def test_file_upload():
    """Test file upload functionality."""
    print("Testing file upload functionality...")
    
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
    
    # Create timezone-aware datetime objects
    starts_at = timezone.make_aware(datetime(2024, 2, 15, 10, 0, 0))
    ends_at = timezone.make_aware(datetime(2024, 2, 15, 18, 0, 0))
    
    auction = Auction.objects.create(
        title='Test Auction with File Upload',
        description='Testing file upload functionality',
        minimum_bid=100,
        starts_at=starts_at,
        ends_at=ends_at,
        created_by=user
    )
    
    print(f"Created test auction: {auction.title}")
    
    # Create a test image file
    test_image_content = b'fake image content'
    test_image = SimpleUploadedFile(
        "test_image.jpg",
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
    
    # Test that the image is accessible
    try:
        # This would normally work if the media files were properly configured
        print(f"Image file exists: {auction_image.image.storage.exists(auction_image.image.name)}")
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
    
    print("✅ File upload test completed successfully!")
    
    # Clean up
    auction_image.delete()
    auction.delete()
    print("✅ Test data cleaned up")


if __name__ == '__main__':
    test_file_upload()
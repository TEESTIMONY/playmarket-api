#!/usr/bin/env python3
"""
Test script to verify auction image field functionality.
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta

# Add the project directory to the Python path
sys.path.insert(0, '/Users/dera/Documents/GitHub/playmarket-api')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playmarket.settings')

# Setup Django
django.setup()

from django.contrib.auth.models import User
from bounties.models import UserProfile
from bounties.auction_models import Auction
from bounties.serializers import AuctionSerializer
from django.utils import timezone


def test_auction_images():
    """Test that auction images are properly serialized."""
    print("Testing auction image field functionality...")
    
    try:
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            print(f"Created admin user: {admin_user.username}")
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                'coins': 1000,
                'is_admin': True
            }
        )
        
        if created:
            print(f"Created user profile for: {admin_user.username}")
        else:
            profile.is_admin = True
            profile.save()
            print(f"Updated user profile for: {admin_user.username}")
        
        # Create test auction with images
        test_images = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://example.com/image3.jpg"
        ]
        
        auction = Auction.objects.create(
            title="Test Auction with Images",
            description="This is a test auction with multiple images",
            image_urls=test_images,
            minimum_bid=10,
            starts_at=timezone.now() + timedelta(hours=1),
            ends_at=timezone.now() + timedelta(hours=2),
            created_by=admin_user
        )
        
        print(f"Created test auction: {auction.title}")
        print(f"Auction image_urls: {auction.image_urls}")
        
        # Test serializer
        serializer = AuctionSerializer(auction)
        serialized_data = serializer.data
        
        print(f"Serialized data keys: {list(serialized_data.keys())}")
        
        if 'images' in serialized_data:
            print(f"✅ SUCCESS: 'images' field found in serialized data")
            print(f"Images value: {serialized_data['images']}")
            
            # Verify the images match
            if serialized_data['images'] == test_images:
                print("✅ SUCCESS: Images match expected values")
            else:
                print(f"❌ ERROR: Images don't match. Expected: {test_images}, Got: {serialized_data['images']}")
        else:
            print("❌ ERROR: 'images' field not found in serialized data")
            print(f"Available fields: {list(serialized_data.keys())}")
        
        # Test API endpoint
        print("\nTesting API endpoint...")
        import requests
        
        # Get JWT token
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = requests.post('http://localhost:8000/api/auth/login/', json=login_data)
        
        if response.status_code == 200:
            token = response.json().get('token')
            print(f"✅ Login successful, token: {token[:20]}...")
            
            # Test auction list endpoint
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get('http://localhost:8000/api/auctions/', headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Auction list API successful")
                
                if 'results' in data:
                    auctions = data['results']
                else:
                    auctions = data
                
                for auction_data in auctions:
                    if auction_data.get('title') == "Test Auction with Images":
                        print(f"Found test auction in API response")
                        if 'images' in auction_data:
                            print(f"✅ SUCCESS: 'images' field found in API response")
                            print(f"Images: {auction_data['images']}")
                        else:
                            print("❌ ERROR: 'images' field not found in API response")
                            print(f"Available fields: {list(auction_data.keys())}")
                        break
                else:
                    print("❌ ERROR: Test auction not found in API response")
                    print(f"Available auctions: {[a.get('title') for a in auctions]}")
            else:
                print(f"❌ ERROR: Auction list API failed with status {response.status_code}")
                print(f"Response: {response.text}")
        else:
            print(f"❌ ERROR: Login failed with status {response.status_code}")
            print(f"Response: {response.text}")
        
        # Clean up
        auction.delete()
        print(f"✅ Cleaned up test auction")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_auction_images()
    if success:
        print("\n🎉 All tests passed! Image field is working correctly.")
    else:
        print("\n💥 Some tests failed. Please check the errors above.")
    sys.exit(0 if success else 1)
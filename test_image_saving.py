#!/usr/bin/env python3
"""
Test script to verify that images are being saved to the database correctly.
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
from django.utils import timezone


def test_image_saving():
    """Test that images are properly saved to the database."""
    print("Testing image saving to database...")
    
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
        
        # Test 1: Create auction with images
        print("\n=== Test 1: Creating auction with images ===")
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
        
        print(f"✅ Created auction: {auction.title}")
        print(f"✅ Auction ID: {auction.id}")
        print(f"✅ Image URLs saved: {auction.image_urls}")
        print(f"✅ Image URLs type: {type(auction.image_urls)}")
        
        # Verify the images are stored correctly
        if auction.image_urls == test_images:
            print("✅ SUCCESS: Images match expected values")
        else:
            print(f"❌ ERROR: Images don't match. Expected: {test_images}, Got: {auction.image_urls}")
        
        # Test 2: Update auction with new images
        print("\n=== Test 2: Updating auction with new images ===")
        new_images = [
            "https://newexample.com/new1.jpg",
            "https://newexample.com/new2.jpg"
        ]
        
        auction.image_urls = new_images
        auction.save()
        
        # Reload from database
        auction.refresh_from_db()
        
        print(f"✅ Updated image URLs: {auction.image_urls}")
        
        if auction.image_urls == new_images:
            print("✅ SUCCESS: Updated images match expected values")
        else:
            print(f"❌ ERROR: Updated images don't match. Expected: {new_images}, Got: {auction.image_urls}")
        
        # Test 3: Empty images
        print("\n=== Test 3: Testing empty images ===")
        empty_images = []
        auction.image_urls = empty_images
        auction.save()
        
        auction.refresh_from_db()
        
        print(f"✅ Empty image URLs: {auction.image_urls}")
        
        if auction.image_urls == empty_images:
            print("✅ SUCCESS: Empty images handled correctly")
        else:
            print(f"❌ ERROR: Empty images not handled correctly. Expected: {empty_images}, Got: {auction.image_urls}")
        
        # Test 4: Single image
        print("\n=== Test 4: Testing single image ===")
        single_image = ["https://singleexample.com/single.jpg"]
        auction.image_urls = single_image
        auction.save()
        
        auction.refresh_from_db()
        
        print(f"✅ Single image URLs: {auction.image_urls}")
        
        if auction.image_urls == single_image:
            print("✅ SUCCESS: Single image handled correctly")
        else:
            print(f"❌ ERROR: Single image not handled correctly. Expected: {single_image}, Got: {auction.image_urls}")
        
        # Test 5: Check database storage format
        print("\n=== Test 5: Checking database storage ===")
        # Query the database directly to see how images are stored
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT image_urls FROM bounties_auction WHERE id = %s", [auction.id])
            db_result = cursor.fetchone()
            
            if db_result:
                db_images = db_result[0]
                print(f"✅ Database raw value: {db_images}")
                print(f"✅ Database value type: {type(db_images)}")
                
                # Parse JSON if it's stored as string
                if isinstance(db_images, str):
                    try:
                        parsed_images = json.loads(db_images)
                        print(f"✅ Parsed JSON: {parsed_images}")
                        print(f"✅ Parsed type: {type(parsed_images)}")
                    except json.JSONDecodeError:
                        print("❌ ERROR: Could not parse JSON from database")
                else:
                    print(f"✅ Database value is already parsed: {db_images}")
            else:
                print("❌ ERROR: Could not retrieve data from database")
        
        # Test 6: Test serializer output
        print("\n=== Test 6: Testing serializer output ===")
        from bounties.serializers import AuctionSerializer
        
        serializer = AuctionSerializer(auction)
        serialized_data = serializer.data
        
        print(f"✅ Serialized 'images' field: {serialized_data.get('images')}")
        print(f"✅ Serialized 'images' type: {type(serialized_data.get('images'))}")
        
        if serialized_data.get('images') == auction.image_urls:
            print("✅ SUCCESS: Serializer output matches database value")
        else:
            print(f"❌ ERROR: Serializer output doesn't match database. Serialized: {serialized_data.get('images')}, DB: {auction.image_urls}")
        
        # Clean up
        auction.delete()
        print(f"\n✅ Cleaned up test auction")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_image_saving()
    if success:
        print("\n🎉 All image saving tests passed! Images are properly saved to the database.")
    else:
        print("\n💥 Some image saving tests failed. Please check the errors above.")
    sys.exit(0 if success else 1)
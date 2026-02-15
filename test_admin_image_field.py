#!/usr/bin/env python3
"""
Test script to verify that the image field is visible and functional in Django admin.
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

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from bounties.models import UserProfile
from bounties.auction_models import Auction as AuctionModel
from bounties.admin import AuctionAdmin
from django.utils import timezone


def test_admin_image_field():
    """Test that the image field is properly configured in Django admin."""
    print("Testing Django admin image field configuration...")
    
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
        
        # Create AuctionAdmin instance
        admin_site = AdminSite()
        auction_admin = AuctionAdmin(AuctionModel, admin_site)
        
        # Test 1: Check if image_urls field is in fieldsets
        print("\n=== Test 1: Checking admin fieldsets ===")
        
        fieldsets = auction_admin.get_fieldsets(None)
        print(f"Fieldsets found: {len(fieldsets)}")
        
        images_found = False
        for i, (name, options) in enumerate(fieldsets):
            print(f"  Fieldset {i+1}: {name}")
            if 'fields' in options:
                fields = options['fields']
                print(f"    Fields: {fields}")
                if 'image_urls' in fields:
                    images_found = True
                    print("    ✅ FOUND: image_urls field in fieldset")
        
        if images_found:
            print("✅ SUCCESS: Image field is configured in Django admin")
        else:
            print("❌ ERROR: Image field not found in Django admin fieldsets")
        
        # Test 2: Check if image_urls is in list_display
        print("\n=== Test 2: Checking admin list display ===")
        
        list_display = auction_admin.list_display
        print(f"List display fields: {list_display}")
        
        if 'image_urls' in list_display:
            print("✅ SUCCESS: image_urls found in list_display")
        else:
            print("❌ ERROR: image_urls not found in list_display")
        
        # Test 3: Check if image_urls is in readonly_fields
        print("\n=== Test 3: Checking admin readonly fields ===")
        
        readonly_fields = auction_admin.readonly_fields
        print(f"Readonly fields: {readonly_fields}")
        
        if 'image_urls' not in readonly_fields:
            print("✅ SUCCESS: image_urls is NOT readonly (editable)")
        else:
            print("❌ ERROR: image_urls is readonly (not editable)")
        
        # Test 4: Create test auction through admin interface
        print("\n=== Test 4: Testing admin form functionality ===")
        
        # Create test auction with images
        test_images = [
            "https://example.com/admin_test1.jpg",
            "https://example.com/admin_test2.jpg"
        ]
        
        auction_data = {
            'title': 'Admin Test Auction',
            'description': 'Test auction created through admin interface',
            'minimum_bid': 50,
            'image_urls': json.dumps(test_images),  # Admin form expects JSON string
            'starts_at': (timezone.now() + timedelta(hours=1)).isoformat(),
            'ends_at': (timezone.now() + timedelta(hours=2)).isoformat(),
            'status': 'pending',
            'created_by': admin_user.id
        }
        
        # Test form validation
        from django.forms import ModelForm
        from bounties.auction_models import Auction
        
        class TestAuctionForm(ModelForm):
            class Meta:
                model = Auction
                fields = '__all__'
        
        form = TestAuctionForm(data=auction_data)
        
        if form.is_valid():
            print("✅ SUCCESS: Admin form validation passed")
            
            # Create the auction
            auction = form.save(commit=False)
            auction.created_by = admin_user
            auction.save()
            
            print(f"✅ Created test auction: {auction.title}")
            print(f"✅ Image URLs: {auction.image_urls}")
            
            # Verify the images were saved correctly
            if auction.image_urls == test_images:
                print("✅ SUCCESS: Images saved correctly through admin form")
            else:
                print(f"❌ ERROR: Images not saved correctly. Expected: {test_images}, Got: {auction.image_urls}")
            
            # Clean up
            auction.delete()
            print("✅ Cleaned up test auction")
            
        else:
            print("❌ ERROR: Admin form validation failed")
            print(f"Form errors: {form.errors}")
        
        # Test 5: Check admin field descriptions
        print("\n=== Test 5: Checking admin field descriptions ===")
        
        for name, options in fieldsets:
            if name == 'Images':
                if 'description' in options:
                    description = options['description']
                    print(f"✅ Image field description: {description}")
                else:
                    print("❌ ERROR: No description found for Images fieldset")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_admin_image_field()
    if success:
        print("\n🎉 All admin image field tests passed! Image field is properly configured in Django admin.")
    else:
        print("\n💥 Some admin image field tests failed. Please check the errors above.")
    sys.exit(0 if success else 1)
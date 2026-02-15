#!/usr/bin/env python3
import requests
import json
import os
import sys
import django
import jwt
import time

# Add the project directory to the Python path
sys.path.append('/Users/dera/Documents/GitHub/playmarket-api')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playmarket.settings')

# Setup Django
django.setup()

from django.contrib.auth.models import User
from bounties.models import UserProfile

def test_single_auction_constraint():
    """Test that only one auction can be active at a time."""
    
    # Get an admin user
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("No admin user found!")
        return
    
    print(f"Testing with admin user: {admin_user.username}")
    
    # Generate JWT token
    secret_key = os.environ.get('SECRET_KEY', 'django-insecure-development-key-for-local-testing-only-not-for-production')
    
    payload = {
        'user_id': admin_user.id,
        'username': admin_user.username,
        'exp': int(time.time()) + 3600,  # Token expires in 1 hour
        'iat': int(time.time())  # Issued at
    }
    
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    print(f"Generated JWT token for user: {admin_user.username}")
    
    # Test 1: Create first auction
    print("\n=== Test 1: Creating first auction ===")
    url = "http://127.0.0.1:8000/bounties/auctions/create/"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    auction_data = {
        "title": "Test Auction 1",
        "description": "First test auction",
        "minimum_bid": 100,
        "starts_at": "2024-02-14T10:00:00Z",
        "ends_at": "2024-02-14T18:00:00Z"
    }
    
    try:
        response = requests.post(url, headers=headers, json=auction_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ First auction created successfully!")
            first_auction = response.json()
            print(f"  Auction ID: {first_auction['id']}")
            print(f"  Title: {first_auction['title']}")
            print(f"  Status: {first_auction['status']}")
        else:
            print("❌ Failed to create first auction!")
            return
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure Django development server is running.")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 2: Try to create second auction (should fail)
    print("\n=== Test 2: Trying to create second auction (should fail) ===")
    auction_data_2 = {
        "title": "Test Auction 2",
        "description": "Second test auction",
        "minimum_bid": 150,
        "starts_at": "2024-02-14T12:00:00Z",
        "ends_at": "2024-02-14T20:00:00Z"
    }
    
    try:
        response = requests.post(url, headers=headers, json=auction_data_2)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            print("✅ Second auction creation correctly blocked!")
            error_data = response.json()
            print(f"  Error: {error_data['error']}")
            if 'active_auction' in error_data:
                active_auction = error_data['active_auction']
                print(f"  Active auction: {active_auction['title']} (ID: {active_auction['id']})")
        else:
            print("❌ Second auction creation should have been blocked!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: End the first auction and try again
    print("\n=== Test 3: Ending first auction and trying again ===")
    end_url = f"http://127.0.0.1:8000/bounties/auctions/{first_auction['id']}/end/"
    
    try:
        response = requests.post(end_url, headers=headers)
        print(f"End auction Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ First auction ended successfully!")
            
            # Now try to create second auction
            response = requests.post(url, headers=headers, json=auction_data_2)
            print(f"Second creation attempt Status Code: {response.status_code}")
            
            if response.status_code == 201:
                print("✅ Second auction created successfully after ending first!")
                second_auction = response.json()
                print(f"  Auction ID: {second_auction['id']}")
                print(f"  Title: {second_auction['title']}")
            else:
                print("❌ Failed to create second auction after ending first!")
                print(f"Response: {response.text}")
        else:
            print("❌ Failed to end first auction!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_single_auction_constraint()
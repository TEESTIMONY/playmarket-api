#!/usr/bin/env python3
import requests
import json
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/dera/Documents/GitHub/playmarket-api')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playmarket.settings')

# Setup Django
django.setup()

from django.contrib.auth.models import User
from bounties.models import UserProfile
from django.contrib.auth.hashers import make_password

def test_auction_creation():
    """Test the auction creation endpoint."""
    
    # Get an admin user
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("No admin user found!")
        return
    
    print(f"Testing with admin user: {admin_user.username}")
    
    # Create a test auction payload
    auction_data = {
        "title": "Test Auction - Limited Edition Sneakers",
        "description": "Rare collectible sneakers in mint condition, size 10",
        "starting_bid": 500,
        "minimum_bid_increment": 50,
        "starts_at": "2024-02-14T10:00:00Z",
        "ends_at": "2024-02-14T18:00:00Z"
    }
    
    # Test the endpoint
    url = "http://127.0.0.1:8000/bounties/auctions/create/"
    
    try:
        response = requests.post(url, json=auction_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Auction creation successful!")
            auction = response.json()
            print(f"Created auction: {auction['title']}")
            print(f"Auction ID: {auction['id']}")
        else:
            print("❌ Auction creation failed!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure Django development server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_auction_creation()
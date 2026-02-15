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

def test_auction_list():
    """Test the auction listing endpoint."""
    
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
    
    # Test the auction list endpoint
    url = "http://127.0.0.1:8000/bounties/auctions/"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Auction list successful!")
            data = response.json()
            auctions = data['results']
            print(f"Found {len(auctions)} auctions")
            for auction in auctions:
                print(f"  - {auction['title']} (ID: {auction['id']}, Status: {auction['status']})")
        else:
            print("❌ Auction list failed!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure Django development server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_auction_list()
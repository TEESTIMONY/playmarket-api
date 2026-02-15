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

def test_auction_permissions():
    """Test auction listing permissions for admin vs regular users."""
    
    # Get an admin user
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("No admin user found!")
        return
    
    print(f"Testing with admin user: {admin_user.username}")
    
    # Generate JWT token for admin
    secret_key = os.environ.get('SECRET_KEY', 'django-insecure-development-key-for-local-testing-only-not-for-production')
    
    payload = {
        'user_id': admin_user.id,
        'username': admin_user.username,
        'exp': int(time.time()) + 3600,  # Token expires in 1 hour
        'iat': int(time.time())  # Issued at
    }
    
    admin_token = jwt.encode(payload, secret_key, algorithm='HS256')
    
    # Test the auction list endpoint as admin
    url = "http://127.0.0.1:8000/bounties/auctions/"
    headers = {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Admin - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Admin sees {data['count']} auctions")
            for auction in data['results']:
                print(f"  - {auction['title']} (ID: {auction['id']}, Status: {auction['status']})")
        else:
            print("❌ Admin auction list failed!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure Django development server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_auction_permissions()
#!/usr/bin/env python3
"""
Debug script to test auction API with admin authentication.
"""

import requests
import json
import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.insert(0, '/Users/dera/Documents/GitHub/playmarket-api')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playmarket.settings')
django.setup()

from django.contrib.auth.models import User
from bounties.models import UserProfile
from bounties.auction_models import Auction

def test_direct_database():
    """Test database directly to see what auctions exist."""
    print("=== Direct Database Test ===")
    
    # Check auctions
    auctions = Auction.objects.all()
    print(f"Total auctions in database: {auctions.count()}")
    for auction in auctions:
        print(f"  ID: {auction.id}, Title: {auction.title}, Status: {auction.status}")
    
    # Check admin user
    admin_user = User.objects.filter(username='admin').first()
    if admin_user:
        try:
            profile = admin_user.profile
            print(f"Admin user: {admin_user.username}, is_admin: {profile.is_admin}")
        except UserProfile.DoesNotExist:
            print("Admin user has no profile")
    
    print()

def test_api_directly():
    """Test the API endpoint directly using Django's test client."""
    print("=== Direct API Test ===")
    
    from django.test import Client
    from django.contrib.auth.models import User
    
    # Create test client
    client = Client()
    
    # Get admin user
    admin_user = User.objects.filter(username='admin').first()
    if not admin_user:
        print("No admin user found")
        return
    
    # Login as admin
    client.force_login(admin_user)
    
    # Test the API endpoint
    response = client.get('/api/auctions/')
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content.decode()}")
    
    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"Found {data.get('count', 0)} auctions")
        for auction in data.get('results', []):
            print(f"  ID: {auction['id']}, Title: {auction['title']}, Status: {auction['status']}")

def test_api_with_jwt():
    """Test the API with JWT authentication."""
    print("=== JWT API Test ===")
    
    # Generate JWT token manually for admin user
    import jwt
    import os
    from django.conf import settings
    
    admin_user = User.objects.filter(username='admin').first()
    if not admin_user:
        print("No admin user found")
        return
    
    # Generate JWT token
    secret_key = settings.SECRET_KEY
    payload = {
        'user_id': admin_user.id,
        'username': admin_user.username,
        'exp': 9999999999  # Far future expiration
    }
    
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    print(f"Generated JWT token: {token[:20]}...")
    
    # Test auction list with token
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get('http://localhost:8000/api/auctions/', headers=headers)
    print(f"Auction list response: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data.get('count', 0)} auctions")
        for auction in data.get('results', []):
            print(f"  ID: {auction['id']}, Title: {auction['title']}")

if __name__ == '__main__':
    print("Debugging auction API...")
    print()
    
    test_direct_database()
    test_api_directly()
    test_api_with_jwt()
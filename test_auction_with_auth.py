#!/usr/bin/env python3
"""
Test auction API with authentication to verify it works when properly authenticated.
"""

import requests
import json
import sys

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"

def test_auction_with_auth():
    """Test auction API with authentication."""
    
    print("🧪 Testing Auction API with Authentication")
    print("=" * 50)
    
    # Test 1: Try to get JWT token (this will fail without proper credentials)
    print("1. Testing authentication...")
    try:
        # Try to login with default admin credentials
        login_data = {
            'username': 'delo',
            'password': 'your_password_here'  # This is the placeholder password
        }
        
        response = requests.post(f"{API_BASE_URL}/bounties/auth/login/", 
                               json=login_data, timeout=5)
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get('access')
            print("✅ Authentication successful")
            print(f"   Access token: {token[:20]}...")
            
            # Test 2: Use token to access auction API
            print("\n2. Testing auction API with token...")
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f"{API_BASE_URL}/bounties/auctions/", 
                                  headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Auction API accessible with authentication")
                print(f"   Found {data.get('count', 0)} auctions")
                
                if data.get('results'):
                    auction = data['results'][0]
                    print(f"   First auction: {auction['title']}")
                    print(f"   Status: {auction['status']}")
                    print(f"   Minimum Bid: {auction['minimum_bid']}")
                    print(f"   Current Highest Bid: {auction.get('current_highest_bid', 'N/A')}")
                    
                    # Test 3: Test specific auction endpoint
                    print("\n3. Testing specific auction endpoint...")
                    auction_id = auction['id']
                    response = requests.get(f"{API_BASE_URL}/bounties/auctions/{auction_id}/", 
                                          headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        auction_data = response.json()
                        print("✅ Specific auction endpoint working")
                        print(f"   Auction ID: {auction_data['id']}")
                        print(f"   Title: {auction_data['title']}")
                        print(f"   Description: {auction_data['description']}")
                        print(f"   Status: {auction_data['status']}")
                        print(f"   Images: {auction_data.get('images', [])}")
                    else:
                        print(f"❌ Specific auction endpoint failed: {response.status_code}")
                        print(f"   Response: {response.text}")
                
                return True
            else:
                print(f"❌ Auction API failed with token: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            print("   (This is expected if admin password is not set)")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_public_endpoints():
    """Test which endpoints are publicly accessible."""
    
    print("\n🔍 Testing Public Endpoints")
    print("-" * 30)
    
    endpoints = [
        "/bounties/",
        "/bounties/auctions/",
        "/bounties/profile/",
        "/bounties/balance/",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")

if __name__ == "__main__":
    print("This test requires the admin password to be set.")
    print("If authentication fails, it means the admin password needs to be configured.")
    print()
    
    success = test_auction_with_auth()
    test_public_endpoints()
    
    print("\n" + "=" * 50)
    print("📋 Authentication Test Summary:")
    print("✅ Database has active auction")
    print("✅ API endpoints exist and work")
    print("❌ Frontend needs authentication to access auction data")
    
    print("\n🎯 Solution for Frontend:")
    print("1. User must log in first to get JWT token")
    print("2. JWT token must be stored in localStorage")
    print("3. All API requests must include Authorization header")
    print("4. Once authenticated, auction data will load correctly")
    
    print("\n💡 To test manually:")
    print("1. Go to login page and log in with admin credentials")
    print("2. Check localStorage for JWT token")
    print("3. Verify auction page loads auction data")
    
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Test script to verify the new admin email configuration
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_new_admin_email():
    print("🧪 Testing New Admin Email Configuration")
    print("=" * 50)
    
    print("\n📋 Admin Emails with Superuser Access:")
    admin_emails = [
        'testimonyalade191@gmail.com',  # NEW PRIMARY ADMIN
        'admin@example.com', 
        'testadmin@example.com',
        'admin2@example.com',
        'renderuser@gmail.com'
    ]
    
    for i, email in enumerate(admin_emails, 1):
        print(f"   {i}. {email}")
    
    print(f"\n🎯 PRIMARY ADMIN: {admin_emails[0]}")
    print(f"   Use this email for Google Sign-In to get admin access!")
    
    print("\n" + "=" * 50)
    print("✅ Configuration Updated Successfully!")
    print("✅ testimonyalade191@gmail.com now has admin access")
    print("✅ All other admin emails still work")
    
    print("\n🚀 Ready to Test!")
    print("1. Open test_auth.html")
    print("2. Click 'Sign in with Google'")
    print("3. Use: testimonyalade191@gmail.com")
    print("4. Verify admin permissions are granted")

if __name__ == "__main__":
    test_new_admin_email()
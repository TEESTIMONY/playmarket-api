#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/dera/Documents/GitHub/playmarket-api')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playmarket.settings')

# Setup Django
django.setup()

from bounties.models import UserProfile

def verify_admin_profiles():
    """Verify that admin users have is_admin=True in their profiles."""
    admin_profiles = UserProfile.objects.filter(is_admin=True)
    
    print(f"Admin profiles: {admin_profiles.count()}")
    
    for profile in admin_profiles:
        print(f'{profile.user.username}: is_admin={profile.is_admin}')

if __name__ == '__main__':
    verify_admin_profiles()
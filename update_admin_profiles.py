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

from django.contrib.auth.models import User
from bounties.models import UserProfile

def update_admin_profiles():
    """Update existing admin users to have is_admin=True in their profiles."""
    admin_users = User.objects.filter(is_superuser=True)
    
    print(f"Found {admin_users.count()} admin users")
    
    for user in admin_users:
        profile, created = UserProfile.objects.get_or_create(user=user)
        if not profile.is_admin:
            profile.is_admin = True
            profile.save()
            print(f'Updated {user.username} with is_admin=True')
        else:
            print(f'{user.username} already has is_admin=True')

if __name__ == '__main__':
    update_admin_profiles()
#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playmarket.settings')
django.setup()

from django.contrib.auth.models import User
from bounties.models import UserProfile, BountyClaim, Bounty

def debug_data():
    print("=== Django Admin Registration Check ===")
    from django.contrib import admin
    registered_models = [model.__name__ for model, admin_class in admin.site._registry.items()]
    print(f"Registered models: {registered_models}")
    
    print("\n=== Database Content Check ===")
    
    # Check Users
    users = User.objects.all()
    print(f"Total users: {users.count()}")
    for user in users:
        print(f"  - {user.username} (ID: {user.id})")
    
    # Check UserProfiles
    profiles = UserProfile.objects.all()
    print(f"Total user profiles: {profiles.count()}")
    for profile in profiles:
        print(f"  - {profile.user.username}: {profile.coin_balance} coins")
    
    # Check Bounties
    bounties = Bounty.objects.all()
    print(f"Total bounties: {bounties.count()}")
    for bounty in bounties:
        print(f"  - {bounty.title} (ID: {bounty.id}) - Reward: {bounty.reward} coins")
    
    # Check Bounty Claims
    claims = BountyClaim.objects.all()
    print(f"Total bounty claims: {claims.count()}")
    for claim in claims:
        print(f"  - User: {claim.user.username}, Bounty: {claim.bounty.title} (ID: {claim.bounty.id}), Status: {claim.status}")

if __name__ == "__main__":
    debug_data()
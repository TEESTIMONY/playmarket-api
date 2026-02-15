#!/usr/bin/env python
"""
Script to create a superuser during deployment
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playmarket.settings')
django.setup()

from django.contrib.auth import get_user_model
from bounties.models import UserProfile

User = get_user_model()

def create_superuser():
    """Create superuser with environment variables"""
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123456')
    
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"✅ Successfully created superuser: {username}")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
    else:
        print(f"⚠️  Superuser {username} already exists")


def sync_admin_identities_from_env():
    """Ensure admin identities from ADMIN_EMAILS have Django/profile admin flags."""
    raw_admins = os.environ.get('ADMIN_EMAILS', '')
    admin_identities = [item.strip().lower() for item in raw_admins.split(',') if item.strip()]

    if not admin_identities:
        print("ℹ️  No ADMIN_EMAILS configured; skipping admin identity sync")
        return

    print(f"ℹ️  Syncing {len(admin_identities)} admin identity(ies) from ADMIN_EMAILS")

    for identity in admin_identities:
        user, created = User.objects.get_or_create(
            username=identity,
            defaults={
                'email': identity,
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
            },
        )

        user_updated = False
        if not user.email:
            user.email = identity
            user_updated = True
        if not user.is_staff:
            user.is_staff = True
            user_updated = True
        if not user.is_superuser:
            user.is_superuser = True
            user_updated = True
        if user_updated:
            user.save(update_fields=['email', 'is_staff', 'is_superuser'])

        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'coin_balance': 0})
        if not profile.is_admin:
            profile.is_admin = True
            profile.save(update_fields=['is_admin'])

        status = "created" if created else "updated"
        print(f"✅ Admin identity {status}: {identity}")

if __name__ == '__main__':
    create_superuser()
    sync_admin_identities_from_env()
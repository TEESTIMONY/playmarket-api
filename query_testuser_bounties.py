#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playmarket.settings')

# Setup Django
django.setup()

from django.contrib.auth.models import User
from bounties.models import BountyClaim

def main():
    try:
        # Find the testuser
        testuser = User.objects.filter(username='testuser').first()
        
        if not testuser:
            print("❌ User 'testuser' not found in the database.")
            return
        
        print(f"✅ Found user: {testuser.username} (ID: {testuser.id})")
        print(f"   Email: {testuser.email}")
        print(f"   Joined: {testuser.date_joined}")
        
        # Get all bounty claims for this user
        bounty_claims = BountyClaim.objects.filter(user=testuser).select_related('bounty').order_by('-approved_at', '-created_at')
        
        if not bounty_claims:
            print("\n📝 No bounty claims found for this user.")
            return
        
        print(f"\n🎯 Found {bounty_claims.count()} bounty claim(s) for {testuser.username}:")
        print("=" * 80)
        
        for i, claim in enumerate(bounty_claims, 1):
            status_emoji = {
                'approved': '✅',
                'rejected': '❌',
                'submitted': '⏳',
                'pending': '⏳'
            }.get(claim.status, '❓')
            
            print(f"\n{i}. {status_emoji} {claim.bounty.title}")
            print(f"   Bounty ID: {claim.bounty.id}")
            print(f"   Reward: {claim.bounty.reward} coins")
            print(f"   Status: {claim.get_status_display()}")
            print(f"   Submitted: {claim.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if claim.submitted_at else 'Not submitted'}")
            print(f"   Approved: {claim.approved_at.strftime('%Y-%m-%d %H:%M:%S') if claim.approved_at else 'Not approved'}")
            print(f"   Created: {claim.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if claim.submission:
                print(f"   Submission: {claim.submission[:100]}{'...' if len(claim.submission) > 100 else ''}")
        
        # Summary statistics
        approved_count = bounty_claims.filter(status='approved').count()
        submitted_count = bounty_claims.filter(status='submitted').count()
        pending_count = bounty_claims.filter(status='pending').count()
        rejected_count = bounty_claims.filter(status='rejected').count()
        
        total_approved_rewards = sum(claim.bounty.reward for claim in bounty_claims if claim.status == 'approved')
        total_pending_rewards = sum(claim.bounty.reward for claim in bounty_claims if claim.status == 'submitted')
        
        print(f"\n📊 SUMMARY STATISTICS:")
        print(f"   Total Claims: {bounty_claims.count()}")
        print(f"   Approved: {approved_count} (Total: {total_approved_rewards} coins)")
        print(f"   Submitted (Waiting): {submitted_count} (Potential: {total_pending_rewards} coins)")
        print(f"   Pending: {pending_count}")
        print(f"   Rejected: {rejected_count}")
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
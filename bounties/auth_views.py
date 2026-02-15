import os
import jwt
import requests
from datetime import datetime, timedelta
import logging
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile

logger = logging.getLogger(__name__)


def _assign_admin_privileges_if_allowed(user, user_email):
    """Grant Django + profile admin flags for approved admin identities."""
    admin_emails_env = os.environ.get('ADMIN_EMAILS', '')
    configured_admin_emails = [
        email.strip().lower() for email in admin_emails_env.split(',') if email.strip()
    ]

    superuser_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip().lower()
    if superuser_email:
        configured_admin_emails.append(superuser_email)

    fallback_admin_emails = [
        'testimonyalade191@gmail.com',
        'admin@example.com',
        'testadmin@example.com',
        'admin2@example.com',
        'renderuser@gmail.com',
    ]

    admin_emails = set(configured_admin_emails or fallback_admin_emails)
    is_allowed_admin = user_email.lower() in admin_emails

    # Also trust existing Django superusers/staff, or any existing superuser
    # that has the same email (common in Render bootstrap workflows).
    is_superuser_email = User.objects.filter(
        email__iexact=user_email,
        is_superuser=True,
    ).exists()

    has_existing_admin_flags = bool(user.is_superuser or user.is_staff)

    should_be_admin = bool(is_allowed_admin or is_superuser_email or has_existing_admin_flags)

    logger.info(
        "Admin mapping for firebase user email=%s should_be_admin=%s allowed_by_env=%s matched_superuser_email=%s existing_admin_flags=%s",
        user_email,
        should_be_admin,
        is_allowed_admin,
        is_superuser_email,
        has_existing_admin_flags,
    )

    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'coin_balance': 0})

    if should_be_admin:
        user_updated = False
        profile_updated = False

        if not user.is_superuser:
            user.is_superuser = True
            user_updated = True
        if not user.is_staff:
            user.is_staff = True
            user_updated = True
        if user_updated:
            user.save(update_fields=['is_superuser', 'is_staff'])

        if not profile.is_admin:
            profile.is_admin = True
            profile_updated = True
        if profile_updated:
            profile.save(update_fields=['is_admin'])

    return profile

# Firebase Admin SDK setup
import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase Admin SDK using environment variables
if not firebase_admin._apps:
    try:
        # Get Firebase credentials from environment variables
        firebase_credentials = {
            'type': os.environ.get('FIREBASE_TYPE', 'service_account'),
            'project_id': os.environ.get('FIREBASE_PROJECT_ID', 'playmarket-6aae1'),
            'private_key_id': os.environ.get('FIREBASE_PRIVATE_KEY_ID', '5edfdd840327b77c4eaa3fc412b6ecd22c1e458c'),
            'private_key': os.environ.get('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
            'client_email': os.environ.get('FIREBASE_CLIENT_EMAIL', 'firebase-adminsdk-fbsvc@playmarket-6aae1.iam.gserviceaccount.com'),
            'client_id': os.environ.get('FIREBASE_CLIENT_ID', ''),
            'auth_uri': os.environ.get('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
            'token_uri': os.environ.get('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
            'auth_provider_x509_cert_url': os.environ.get('FIREBASE_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
            'client_x509_cert_url': os.environ.get('FIREBASE_CLIENT_X509_CERT_URL', ''),
            'universe_domain': os.environ.get('FIREBASE_UNIVERSE_DOMAIN', 'googleapis.com')
        }
        
        # Validate required credentials
        required_fields = ['private_key', 'client_email', 'project_id']
        missing_fields = [field for field in required_fields if not firebase_credentials[field]]
        
        if missing_fields:
            print(f"Firebase initialization error: Missing required environment variables: {', '.join(missing_fields)}")
            print("Please set the following environment variables:")
            print("- FIREBASE_PRIVATE_KEY")
            print("- FIREBASE_CLIENT_EMAIL") 
            print("- FIREBASE_PROJECT_ID")
        else:
            # Initialize Firebase with credentials dictionary
            cred = credentials.Certificate(firebase_credentials)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully using environment variables")
            
    except Exception as e:
        print(f"Firebase initialization error: {e}")
        print("Please ensure all Firebase environment variables are properly set")


def generate_jwt_token(user):
    """Generate JWT token for user"""
    payload = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow(),
    }
    return jwt.encode(payload, os.environ.get('SECRET_KEY', 'django-insecure-development-key-for-local-testing-only-not-for-production'), algorithm='HS256')


def verify_jwt_token(token):
    """Verify JWT token and return user"""
    try:
        payload = jwt.decode(
            token, 
            os.environ.get('SECRET_KEY', 'django-insecure-development-key-for-local-testing-only-not-for-production'), 
            algorithms=['HS256']
        )
        user = User.objects.get(id=payload['user_id'])
        return user
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except User.DoesNotExist:
        return None


@api_view(['POST'])
@permission_classes([AllowAny])
def firebase_login(request):
    """Login with Firebase ID token"""
    firebase_token = request.data.get('id_token')
    
    if not firebase_token:
        return Response({'error': 'Firebase ID token is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Verify Firebase ID token
        decoded_token = auth.verify_id_token(firebase_token, clock_skew_seconds=60)
        user_email = decoded_token['email']
        user_name = decoded_token.get('name', '')
        firebase_uid = decoded_token['uid']
        
        # Get or create Django user
        user, created = User.objects.get_or_create(
            username=user_email,
            defaults={
                'email': user_email,
                'first_name': user_name,
                'is_active': True
            }
        )
        
        # Ensure profile exists and map allowed admin emails to Django/profile admin flags
        profile = _assign_admin_privileges_if_allowed(user, user_email)
        
        # Generate JWT token for frontend
        jwt_token = generate_jwt_token(user)
        
        return Response({
            'token': jwt_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'is_new': created,
                'is_admin': bool(user.is_superuser or user.is_staff or getattr(profile, 'is_admin', False)),
            },
            'message': 'Login successful'
        })
        
    except auth.ExpiredIdTokenError:
        return Response({'error': 'Firebase ID token expired. Please sign in again.'}, status=status.HTTP_400_BAD_REQUEST)
    except auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid Firebase ID token: {str(e)}")
        error_payload = {'error': 'Invalid Firebase ID token'}
        if settings.DEBUG:
            error_payload['details'] = str(e)
        return Response(error_payload, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception(f"Firebase authentication failed: {str(e)}")
        return Response({'error': f'Authentication failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_token(request):
    """Verify JWT token"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = verify_jwt_token(token)
    if user:
        return Response({
            'valid': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
    else:
        return Response({'valid': False, 'error': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def logout(request):
    """Logout user (client-side token removal is sufficient)"""
    return Response({'message': 'Logout successful'})


class FirebaseAuthentication:
    """Custom authentication class for Firebase JWT tokens"""
    
    def authenticate(self, request):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return None
            
        user = verify_jwt_token(token)
        if user:
            return (user, None)
        
        return None
    
    def authenticate_header(self, request):
        return 'Bearer'


@api_view(['GET'])
def get_user_profile(request):
    """Get current user profile"""
    user = request.user
    profile = user.profile
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined
        },
        'profile': {
            'coin_balance': profile.coin_balance
        }
    })
import os
import jwt
import requests
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile

# Firebase Admin SDK setup
import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    try:
        # Use the service account key file
        cred = credentials.Certificate('firebase_service_account.json')
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Firebase initialization error: {e}")


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
        decoded_token = auth.verify_id_token(firebase_token)
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
        
        # Grant admin permissions to specific email addresses
        admin_emails = [
            'testimonyalade191@gmail.com',
            'admin@example.com', 
            'testadmin@example.com',
            'admin2@example.com',
            'renderuser@gmail.com'
        ]
        
        if user_email in admin_emails:
            user.is_superuser = True
            user.is_staff = True
            user.save()
        
        # Create UserProfile if it doesn't exist
        UserProfile.objects.get_or_create(user=user, defaults={'coin_balance': 0})
        
        # Generate JWT token for frontend
        jwt_token = generate_jwt_token(user)
        
        return Response({
            'token': jwt_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'is_new': created
            },
            'message': 'Login successful'
        })
        
    except auth.InvalidIdTokenError:
        return Response({'error': 'Invalid Firebase ID token'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
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
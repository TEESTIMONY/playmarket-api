import os
import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User


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


class FirebaseAuthentication(BaseAuthentication):
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
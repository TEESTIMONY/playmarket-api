"""
JWT authentication middleware for Django Channels WebSocket connections.

Allows frontend clients to authenticate using the same JWT token used by REST
API requests by passing it as a `token` query parameter.
"""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

from .authentication import verify_jwt_token


@database_sync_to_async
def get_user_from_token(token):
    user = verify_jwt_token(token)
    return user or AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    """Attach authenticated user to WebSocket scope using JWT token."""

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        token = params.get('token', [None])[0]

        # Optional fallback to Authorization header if present.
        if not token:
            headers = dict(scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode()
            if auth_header.lower().startswith('bearer '):
                token = auth_header.split(' ', 1)[1].strip()

        scope['user'] = await get_user_from_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)

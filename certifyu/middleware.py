"""Lightweight per-IP rate limiter for the OAuth2 token endpoint.

Backed by Django's local-memory cache — protects per process only, but is a
zero-dependency baseline. For multi-worker / multi-host installs, swap the
cache backend to Redis or add an upstream WAF rule.
"""
import time

from django.core.cache import cache
from django.http import JsonResponse


THROTTLED_PATHS = ('/auth/token', '/auth/convert-token', '/users/CreateUserProfile',
                   '/users/password-reset/request', '/users/password-reset/verify',
                   '/users/password-reset/confirm')
WINDOW_SECONDS  = 60
MAX_HITS        = 20  # per (IP, path) per window


def _client_ip(request):
    fwd = request.META.get('HTTP_X_FORWARDED_FOR')
    return (fwd.split(',')[0].strip() if fwd else request.META.get('REMOTE_ADDR', '')) or 'unknown'


class AuthRateLimitMiddleware:
    """Throttle POSTs to known auth endpoints by IP."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST' and request.path in THROTTLED_PATHS:
            ip = _client_ip(request)
            key = f'rl:auth:{request.path}:{ip}'
            count = cache.get(key, 0) + 1
            cache.set(key, count, WINDOW_SECONDS)
            if count > MAX_HITS:
                return JsonResponse(
                    {'error': 'rate_limited',
                     'detail': 'Too many requests, please slow down.'},
                    status=429,
                    headers={'Retry-After': str(WINDOW_SECONDS)},
                )
        return self.get_response(request)

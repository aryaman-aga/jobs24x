"""Production middleware for rate limiting, security, and monitoring."""

import time
import threading
from collections import defaultdict
from django.http import JsonResponse
from django.conf import settings


class RateLimitMiddleware:
    """Simple in-memory rate limiter (use Redis in production)."""

    def __init__(self, get_response):
        self.get_response = get_response
        self._lock = threading.Lock()
        self._requests = defaultdict(list)
        self._limit = getattr(settings, 'RATE_LIMIT_REQUESTS', 60)
        self._window = getattr(settings, 'RATE_LIMIT_WINDOW', 60)

    def __call__(self, request):
        if settings.DEBUG:
            return self.get_response(request)

        ip = request.META.get('REMOTE_ADDR', 'unknown')
        now = time.time()

        with self._lock:
            self._requests[ip] = [
                t for t in self._requests[ip]
                if now - t < self._window
            ]
            if len(self._requests[ip]) >= self._limit:
                return JsonResponse(
                    {'error': 'Too many requests. Please slow down.'},
                    status=429
                )
            self._requests[ip].append(now)

        return self.get_response(request)


class RequestTimingMiddleware:
    """Logs request duration for performance monitoring."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration = time.time() - start

        if duration > 0.5:
            import logging
            logger = logging.getLogger('django.request')
            logger.warning(
                'Slow request: %s %s (%.2fs)',
                request.method, request.path, duration
            )

        response['X-Response-Time'] = f'{duration:.3f}s'
        return response


class SecurityHeadersMiddleware:
    """Adds security headers to all responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

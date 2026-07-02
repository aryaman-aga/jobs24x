"""Caching utilities for high-traffic endpoints."""

from functools import wraps
from django.core.cache import cache
from django.conf import settings
from django.utils.hashable import make_hashable
import hashlib
import json


def cache_page(timeout=300, key_prefix=''):
    """Decorator to cache view responses in Redis/Memcache.

    Usage:
        @cache_page(timeout=300)
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if settings.DEBUG:
                return view_func(request, *args, **kwargs)

            parts = [key_prefix, request.path, request.GET.urlencode()]
            for k, v in kwargs.items():
                parts.append(f'{k}={v}')
            if request.user.is_authenticated:
                parts.append(f'user={request.user.id}')

            cache_key = 'view:' + hashlib.md5(
                ''.join(parts).encode()
            ).hexdigest()

            cached = cache.get(cache_key)
            if cached is not None:
                return cached

            response = view_func(request, *args, **kwargs)

            if hasattr(response, 'render') and callable(response.render):
                response.render()
            cache.set(cache_key, response, timeout)

            return response
        return _wrapped_view
    return decorator


def cache_queryset(timeout=600):
    """Cache a queryset result.

    Usage:
        @cache_queryset(timeout=300)
        def get_active_jobs():
            return list(Job.objects.filter(is_active=True)[:100])
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = 'qs:' + func.__name__ + ':' + hashlib.md5(
                json.dumps({'args': str(args), 'kwargs': str(kwargs)}, sort_keys=True).encode()
            ).hexdigest()

            result = cache.get(cache_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator


def invalidate_cache(pattern=''):
    """Invalidate cache entries matching a pattern."""
    if hasattr(cache, 'delete_pattern'):
        cache.delete_pattern(f'*{pattern}*')
    else:
        cache.clear()

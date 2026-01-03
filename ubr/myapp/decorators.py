# from functools import wraps
# from django.http import HttpResponseForbidden

# from .models import Profile


# def role_required(role):
#     """Decorator to require a specific Profile.user_type for a view.

#     Returns HTTP 403 when the logged-in user does not have the required role.
#     """
#     def decorator(view_func):
#         @wraps(view_func)
#         def _wrapped(request, *args, **kwargs):
#             # Try attribute access first (Django OneToOne creates `user.profile`),
#             # otherwise fetch to be robust.
#             profile = getattr(request.user, 'profile', None)
#             if profile is None:
#                 try:
#                     profile = Profile.objects.get(user=request.user)
#                 except Exception:
#                     profile = None

#             if profile and profile.user_type == role:
#                 return view_func(request, *args, **kwargs)
#             return HttpResponseForbidden('Forbidden: insufficient permissions')

#         return _wrapped

#     return decorator

# from django.contrib.auth import logout
# from django.shortcuts import redirect
# from django.contrib import messages
# from django.views.decorators.cache import never_cache

# @never_cache
# def custom_logout(request):
#     """
#     Enhanced logout that clears session and prevents caching.
#     """
#     # Clear all messages
#     storage = messages.get_messages(request)
#     storage.used = True
    
#     # Logout user
#     logout(request)
    
#     # Add success message
#     messages.success(request, 'You have been logged out successfully.')
    
#     # Create response with cache prevention headers
#     response = redirect('home')
#     response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
#     response['Pragma'] = 'no-cache'
#     response['Expires'] = '0'
    
#     return response



from functools import wraps
from django.http import HttpResponseForbidden
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from .models import Profile


def no_cache(view_func):
    """
    Decorator to prevent caching of views.
    Use on dashboard and other sensitive views.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    return _wrapped


def role_required(role):
    """Decorator to require a specific Profile.user_type for a view.

    Returns HTTP 403 when the logged-in user does not have the required role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            # Try attribute access first (Django OneToOne creates `user.profile`),
            # otherwise fetch to be robust.
            profile = getattr(request.user, 'profile', None)
            if profile is None:
                try:
                    profile = Profile.objects.get(user=request.user)
                except Exception:
                    profile = None

            if profile and profile.user_type == role:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden('Forbidden: insufficient permissions')

        return _wrapped

    return decorator
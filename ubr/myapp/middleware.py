from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Middleware to prevent cached page access after logout and ensure
    proper session validation.
    """
    
    def process_response(self, request, response):
        """
        Add cache-control headers to prevent browser caching of sensitive pages.
        This prevents users from accessing pages via the back button after logout.
        """
        if request.user.is_authenticated:
            # For authenticated users, prevent caching of protected pages
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response


class LoginRequiredMiddleware(MiddlewareMixin):
    """
    Middleware to require login for all views except public ones.
    """
    
    # URLs that don't require authentication
    EXEMPT_URLS = [
        reverse('home'),
        reverse('login'),
        reverse('signup'),
        '/admin/login/',  # Django admin login
    ]
    
    def process_request(self, request):
        """
        Check if user is authenticated for protected URLs.
        """
        # Get the current path
        path = request.path_info
        
        # Check if the path is exempt from authentication
        if any(path.startswith(exempt) for exempt in self.EXEMPT_URLS):
            return None
        
        # Check if path is for static/media files
        if path.startswith('/static/') or path.startswith('/media/'):
            return None
        
        # If user is not authenticated, redirect to login
        if not request.user.is_authenticated:
            return redirect('login')
        
        return None
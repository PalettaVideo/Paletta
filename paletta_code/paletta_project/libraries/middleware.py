from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from .models import Library
import logging

logger = logging.getLogger(__name__)

class LibraryContextMiddleware(MiddlewareMixin):
  """
  Middleware to handle library context consistently across all requests.
  Ensures that every request has access to the current library context.
  """
  def process_request(self, request):
    """
    Process the request to determine the current library context.
    Priority: URL slug > Session > Default Paletta library
    """
    current_library = None
    url_library_slug = None
    
    # Try to get library from URL kwargs (highest priority)
    if hasattr(request, 'resolver_match') and request.resolver_match:
      url_library_slug = request.resolver_match.kwargs.get('library_slug')
    
    # If no resolver match kwargs, try to extract from URL path directly
    if not url_library_slug:
      path_parts = request.path.strip('/').split('/')
      if len(path_parts) >= 2 and path_parts[0] == 'library':
        url_library_slug = path_parts[1]
        logger.debug(f"Extracted library slug from URL path: {url_library_slug}")
    
    # Try to find the library by slug
    if url_library_slug:
      current_library = self.get_library_by_slug(url_library_slug)
      if current_library:
        # Update session to maintain context
        request.session['current_library_id'] = current_library.id
        logger.debug(f"Library context set from URL: {current_library.name} (slug: {url_library_slug})")
      else:
        logger.warning(f"Library not found for slug: {url_library_slug}")
  
    # Fallback to session if no URL slug or library not found
    if not current_library:
      library_id = request.session.get('current_library_id')
      if library_id:
        try:
          current_library = Library.objects.get(id=library_id, is_active=True)
          logger.debug(f"Library context from session: {current_library.name}")
        except Library.DoesNotExist:
          # Clean up invalid session data
          request.session.pop('current_library_id', None)
          logger.warning(f"Invalid library ID in session: {library_id}")
    
    # Final fallback to default Paletta library
    if not current_library:
      try:
        current_library = Library.objects.get(name='Paletta', is_active=True)
        request.session['current_library_id'] = current_library.id
        logger.debug("Using default Paletta library")
      except Library.DoesNotExist:
        logger.error("Default Paletta library not found!")
  
    # CLEAN APPROACH: Only attach current_library to request
    request.current_library = current_library
    
    # Store the extracted URL slug for debugging
    request.url_library_slug = url_library_slug
    
    # For authenticated users, get all available libraries ordered by creation date
    if request.user.is_authenticated:
      request.all_libraries = Library.objects.filter(is_active=True).order_by('created_at')
    else:
      request.all_libraries = Library.objects.none()
    
    return None
  
  def get_library_by_slug(self, slug):
    """Get a library by its slug."""
    try:
      # Try exact match first
      libraries = Library.objects.filter(is_active=True)
      for library in libraries:
        if slugify(library.name) == slug:
          return library
      return None
    except Exception as e:
      logger.error(f"Error getting library by slug: {e}")
      return None
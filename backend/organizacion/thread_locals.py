from threading import local

_thread_locals = local()

def get_current_organization():
    """
    Returns the organization for the current request, or None if not set.
    """
    return getattr(_thread_locals, 'organization', None)

def set_current_organization(organization):
    """
    Sets the organization for the current request.
    """
    _thread_locals.organization = organization

"""
Custom throttling classes for the citas app.
"""
from rest_framework.throttling import UserRateThrottle


class StaffRateThrottle(UserRateThrottle):
    """
    Custom throttle for staff users.
    Staff users get a higher rate limit than regular users.
    """
    scope = 'staff'

    def allow_request(self, request, view):
        # If user is staff, use the staff rate
        if request.user and request.user.is_authenticated and request.user.is_staff:
            self.scope = 'staff'
            return super().allow_request(request, view)
        # Otherwise, use default user rate
        return True  # Let the UserRateThrottle handle it

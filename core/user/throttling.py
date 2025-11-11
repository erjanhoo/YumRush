"""
Custom throttling classes for rate limiting OTP-related endpoints.
Protects against brute force attacks on OTP verification and OTP resend operations.
"""

from rest_framework.throttling import SimpleRateThrottle
from django.core.cache import cache


class OTPVerificationThrottle(SimpleRateThrottle):
    """
    Throttle for OTP verification attempts.
    Limits: 5 attempts per minute, 10 attempts per hour per IP/user.
    This prevents brute force attacks on OTP codes.
    """
    scope = 'otp_verification'
    
    def get_cache_key(self, request, view):
        """
        Generate cache key based on user_id from request data and IP address.
        This ensures throttling is applied per user/IP combination.
        """
        # Try to get user_id from request data
        user_id = request.data.get('user_id', None)
        
        if user_id:
            # Throttle by user_id + IP for better security
            ident = f"{user_id}_{self.get_ident(request)}"
        else:
            # Fall back to IP-based throttling
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
    
    def throttle_failure(self):
        """
        Called when a request is throttled.
        Can be used to log suspicious activity.
        """
        # Optional: Add logging here for security monitoring
        return super().throttle_failure()


class OTPResendThrottle(SimpleRateThrottle):
    """
    Throttle for OTP resend requests.
    Limits: 3 attempts per minute, 10 attempts per hour per user.
    Prevents spam and potential DoS attacks via email flooding.
    """
    scope = 'otp_resend'
    
    def get_cache_key(self, request, view):
        """
        Generate cache key based on email/user_id from request data.
        This prevents users from spamming OTP resend requests.
        """
        # Try to get email or user_id from request data
        email = request.data.get('email', None)
        user_id = request.data.get('user_id', None)
        
        if email:
            ident = email
        elif user_id:
            ident = f"user_{user_id}"
        else:
            # Fall back to IP-based throttling
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class StrictOTPVerificationThrottle(SimpleRateThrottle):
    """
    More strict throttle for OTP verification after multiple failures.
    Can be applied in addition to OTPVerificationThrottle for extra security.
    Limits: 3 attempts per 5 minutes per user_id.
    """
    scope = 'otp_verification_strict'
    
    def get_cache_key(self, request, view):
        user_id = request.data.get('user_id', None)
        
        if user_id:
            ident = str(user_id)
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class AccountLockoutThrottle(SimpleRateThrottle):
    """
    Account lockout mechanism for repeated failed OTP attempts.
    Limits: 15 attempts per day per user_id.
    After exceeding this limit, the account should be locked or require admin intervention.
    """
    scope = 'otp_account_lockout'
    
    def get_cache_key(self, request, view):
        user_id = request.data.get('user_id', None)
        
        if not user_id:
            return None
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': str(user_id)
        }
    
    def allow_request(self, request, view):
        """
        Check if request should be allowed.
        Returns False if daily limit is exceeded.
        """
        if self.get_cache_key(request, view) is None:
            return True
        
        allowed = super().allow_request(request, view)
        
        if not allowed:
            # Optional: Trigger account lockout notification
            self._trigger_lockout_warning(request)
        
        return allowed
    
    def _trigger_lockout_warning(self, request):
        """
        Optional: Send warning email or notification about potential brute force attack.
        """
        # Implement notification logic here if needed
        pass


class IPBasedOTPThrottle(SimpleRateThrottle):
    """
    IP-based throttle for OTP operations.
    Limits: 20 OTP verifications per hour per IP.
    Prevents distributed brute force attacks from single IP.
    """
    scope = 'otp_ip_based'
    
    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


def check_otp_attempt_limit(user_id, max_attempts=5):
    """
    Utility function to manually check OTP attempt limits.
    Can be used within views for additional validation.
    
    Args:
        user_id: The user ID attempting OTP verification
        max_attempts: Maximum allowed attempts (default: 5)
    
    Returns:
        tuple: (allowed: bool, attempts_left: int)
    """
    cache_key = f'otp_manual_check_{user_id}'
    attempts = cache.get(cache_key, 0)
    
    if attempts >= max_attempts:
        return False, 0
    
    return True, max_attempts - attempts


def increment_otp_attempt(user_id, timeout=3600):
    """
    Utility function to manually increment OTP attempt counter.
    
    Args:
        user_id: The user ID attempting OTP verification
        timeout: Cache timeout in seconds (default: 1 hour)
    """
    cache_key = f'otp_manual_check_{user_id}'
    attempts = cache.get(cache_key, 0)
    cache.set(cache_key, attempts + 1, timeout)


def reset_otp_attempts(user_id):
    """
    Utility function to reset OTP attempt counter.
    Should be called after successful OTP verification.
    
    Args:
        user_id: The user ID whose attempts should be reset
    """
    cache_key = f'otp_manual_check_{user_id}'
    cache.delete(cache_key)

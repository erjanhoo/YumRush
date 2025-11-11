"""
Test throttling functionality for OTP endpoints.
Run with: python manage.py test user.test_throttling
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from user.models import TemporaryRegistration
from django.utils import timezone
from django.contrib.auth.hashers import make_password

User = get_user_model()


class OTPThrottlingTestCase(TestCase):
    """Test OTP verification and resend throttling"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create a temporary registration for testing
        self.temp_reg = TemporaryRegistration.objects.create(
            username='testuser',
            email='test@example.com',
            password=make_password('password123'),
            otp='123456',
            otp_created_at=timezone.now()
        )
        
        # Create a user with 2FA enabled
        self.user = User.objects.create(
            username='testuser2fa',
            email='test2fa@example.com',
            is_2fa_enabled=True
        )
        self.user.set_password('password123')
        self.user.otp = '654321'
        self.user.otp_created_at = timezone.now()
        self.user.save()
    
    def test_otp_verification_throttling(self):
        """Test that OTP verification is throttled after multiple attempts"""
        url = '/api/user/registration_otp_verification/'
        
        # Make requests up to the limit
        for i in range(5):
            response = self.client.post(url, {
                'user_id': self.temp_reg.id,
                'otp_code': '000000'  # Wrong OTP
            })
            # First 5 should go through (might fail validation but not throttled)
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        
        # The 6th request should be throttled
        response = self.client.post(url, {
            'user_id': self.temp_reg.id,
            'otp_code': '000000'
        })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    def test_otp_resend_throttling(self):
        """Test that OTP resend is throttled after multiple attempts"""
        url = '/api/user/resend_registration_otp/'
        
        # Make requests up to the limit (3 per minute)
        for i in range(3):
            response = self.client.post(url, {
                'user_id': self.temp_reg.id
            })
            # First 3 should go through
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])
        
        # The 4th request should be throttled
        response = self.client.post(url, {
            'user_id': self.temp_reg.id
        })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    def test_login_otp_resend_throttling(self):
        """Test that login OTP resend is throttled"""
        url = '/api/user/resend_login_otp/'
        
        # Make requests up to the limit
        for i in range(3):
            response = self.client.post(url, {
                'user_id': self.user.id
            })
            # First 3 should go through
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])
        
        # The 4th request should be throttled
        response = self.client.post(url, {
            'user_id': self.user.id
        })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    def test_different_ips_not_throttled_together(self):
        """Test that throttling is per-IP/user, not global"""
        url = '/api/user/registration_otp_verification/'
        
        # Create another temp registration
        temp_reg2 = TemporaryRegistration.objects.create(
            username='testuser2',
            email='test2@example.com',
            password=make_password('password123'),
            otp='123456',
            otp_created_at=timezone.now()
        )
        
        # Make requests for first user
        for i in range(5):
            self.client.post(url, {
                'user_id': self.temp_reg.id,
                'otp_code': '000000'
            })
        
        # Requests for second user should still work (different user_id)
        response = self.client.post(url, {
            'user_id': temp_reg2.id,
            'otp_code': '000000'
        })
        self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class OTPUtilityFunctionsTestCase(TestCase):
    """Test OTP utility functions"""
    
    def test_check_and_increment_otp_attempts(self):
        """Test manual OTP attempt checking"""
        from user.throttling import check_otp_attempt_limit, increment_otp_attempt, reset_otp_attempts
        
        user_id = 123
        
        # Should allow initially
        allowed, attempts_left = check_otp_attempt_limit(user_id)
        self.assertTrue(allowed)
        self.assertEqual(attempts_left, 5)
        
        # Increment attempts
        for i in range(5):
            increment_otp_attempt(user_id)
        
        # Should be blocked now
        allowed, attempts_left = check_otp_attempt_limit(user_id)
        self.assertFalse(allowed)
        self.assertEqual(attempts_left, 0)
        
        # Reset should allow again
        reset_otp_attempts(user_id)
        allowed, attempts_left = check_otp_attempt_limit(user_id)
        self.assertTrue(allowed)
        self.assertEqual(attempts_left, 5)

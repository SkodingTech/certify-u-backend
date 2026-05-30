"""Email-OTP based password reset.

Flow (all endpoints are public / AllowAny):
  1. POST /users/password-reset/request  {email}                 -> emails a 6-digit code
  2. POST /users/password-reset/verify   {email, otp}            -> checks the code (optional UX step)
  3. POST /users/password-reset/confirm  {email, otp, new_password} -> sets the new password

Security notes:
  * The plaintext OTP is never stored — only a SHA-256 hash (see PasswordResetOTP).
  * Codes are single-use, expire after PASSWORD_RESET_OTP_TTL_MINUTES, and lock
    after PASSWORD_RESET_OTP_MAX_ATTEMPTS wrong guesses.
  * The request step always returns the same generic message to avoid leaking
    whether an account exists (account-enumeration resistance).
  * Per-email and per-IP throttling guard against brute force (the IP guard is
    in certifyu.middleware.AuthRateLimitMiddleware).
"""
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response

from users.models.user import PasswordResetOTP

logger = logging.getLogger('django')

GENERIC_SENT_MESSAGE = (
    "If an account exists for that email, a verification code has been sent."
)

OTP_TTL_MINUTES = getattr(settings, 'PASSWORD_RESET_OTP_TTL_MINUTES', 10)
OTP_MAX_ATTEMPTS = getattr(settings, 'PASSWORD_RESET_OTP_MAX_ATTEMPTS', 5)

# Per-email request throttle: at most REQUEST_THROTTLE_MAX emails per hour.
REQUEST_THROTTLE_MAX = 5
REQUEST_THROTTLE_WINDOW = 3600  # seconds


def _normalize_email(email):
    return (email or "").strip().lower()


def _generate_otp():
    """Cryptographically-random 6-digit code (000000-999999)."""
    return f"{secrets.randbelow(1_000_000):06d}"


def _send_otp_email(email, otp, user=None):
    name = (getattr(user, 'first_name', '') or '').strip() or 'there'
    subject = "Your Certify-U password reset code"
    text_body = (
        f"Hi {name},\n\n"
        f"We received a request to reset your Certify-U password.\n\n"
        f"Your verification code is: {otp}\n\n"
        f"This code expires in {OTP_TTL_MINUTES} minutes. Enter it on the "
        f"password reset page to choose a new password.\n\n"
        f"If you didn't request this, you can safely ignore this email — your "
        f"password will stay the same.\n\n"
        f"— The Certify-U Team"
    )
    # Render via the shared branded template (logo + brand styling). Errors
    # propagate (fail_silently=False) so existing OTP send-failure handling
    # is preserved.
    from courses.services.notifications import notify_password_reset_otp
    notify_password_reset_otp(
        email=email,
        otp=otp,
        name=name,
        ttl_minutes=OTP_TTL_MINUTES,
        subject=subject,
        text_body=text_body,
    )


def _match_active_otp(email, otp):
    """Validate (email, otp). Returns (record, error_response).

    On a wrong guess the attempt counter is incremented; on expiry/lockout the
    record is consumed so it can't be reused.
    """
    otp = (otp or "").strip()
    if not email or not otp:
        return None, Response(
            {'error': 'Email and verification code are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    record = (
        PasswordResetOTP.objects
        .filter(email=email, is_used=False)
        .order_by('-id')
        .first()
    )
    if record is None:
        return None, Response(
            {'error': 'Invalid or expired code. Please request a new one.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if record.is_expired():
        record.is_used = True
        record.save(update_fields=['is_used'])
        return None, Response(
            {'error': 'This code has expired. Please request a new one.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if record.attempts >= OTP_MAX_ATTEMPTS:
        record.is_used = True
        record.save(update_fields=['is_used'])
        return None, Response(
            {'error': 'Too many incorrect attempts. Please request a new code.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    if record.otp_hash != PasswordResetOTP.hash_otp(otp):
        record.attempts += 1
        record.save(update_fields=['attempts'])
        remaining = max(OTP_MAX_ATTEMPTS - record.attempts, 0)
        return None, Response(
            {'error': f'Incorrect code. {remaining} attempt(s) remaining.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return record, None


def RequestPasswordResetOTP(request):
    email = _normalize_email(request.data.get('email'))
    if not email:
        return Response(
            {'error': 'Email is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Per-email throttle (independent of the per-IP middleware guard).
    throttle_key = f'pwdreset:req:{email}'
    count = cache.get(throttle_key, 0)
    if count >= REQUEST_THROTTLE_MAX:
        # Stay generic — don't reveal the account exists.
        return Response({'detail': GENERIC_SENT_MESSAGE}, status=status.HTTP_200_OK)
    cache.set(throttle_key, count + 1, REQUEST_THROTTLE_WINDOW)

    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is not None:
        # Invalidate any outstanding codes before issuing a fresh one.
        PasswordResetOTP.objects.filter(email=email, is_used=False).update(is_used=True)
        otp = _generate_otp()
        PasswordResetOTP.objects.create(
            user=user,
            email=email,
            otp_hash=PasswordResetOTP.hash_otp(otp),
            expires_at=timezone.now() + timedelta(minutes=OTP_TTL_MINUTES),
        )
        try:
            _send_otp_email(email, otp, user)
        except Exception as exc:  # SMTP / config failure — log, stay generic.
            logger.error("Password-reset OTP email failed for %s: %s", email, exc)

    return Response({'detail': GENERIC_SENT_MESSAGE}, status=status.HTTP_200_OK)


def VerifyPasswordResetOTP(request):
    email = _normalize_email(request.data.get('email'))
    otp = request.data.get('otp') or request.data.get('code')
    record, err = _match_active_otp(email, otp)
    if err is not None:
        return err
    # Valid — do NOT consume here; the confirm step re-validates and consumes it.
    return Response(
        {'detail': 'Code verified. You can now set a new password.', 'verified': True},
        status=status.HTTP_200_OK,
    )


def ConfirmPasswordReset(request):
    email = _normalize_email(request.data.get('email'))
    otp = request.data.get('otp') or request.data.get('code')
    new_password = request.data.get('new_password') or request.data.get('password')

    if not new_password:
        return Response(
            {'error': 'A new password is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    record, err = _match_active_otp(email, otp)
    if err is not None:
        return err

    user = record.user
    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as exc:
        return Response(
            {'error': ' '.join(exc.messages)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(new_password)
    user.save(update_fields=['password'])

    # Consume this code and any other outstanding ones for the account.
    record.is_used = True
    record.save(update_fields=['is_used'])
    PasswordResetOTP.objects.filter(email=email, is_used=False).update(is_used=True)
    cache.delete(f'pwdreset:req:{email}')

    return Response(
        {'detail': 'Your password has been reset. You can now sign in.'},
        status=status.HTTP_200_OK,
    )

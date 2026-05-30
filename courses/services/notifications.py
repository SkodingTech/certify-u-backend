"""Email notification helpers.

Each notification renders a branded HTML template (templates/emails/*.html) with
a plain-text fallback, sent via EmailMultiAlternatives. Sends are best-effort by
default (fail_silently) so a flaky SMTP config never blocks a request — the one
exception is the password-reset OTP, which propagates errors to its caller.

Recipients:
  * Admin   -> settings.ADMIN_NOTIFICATION_EMAIL (new users, new/updated courses,
               new enrolments/payments, security events).
  * Student -> enrolment, certificate, assessment result, booking confirmation.
  * Trainer -> course created, document review, password reset (shared).
"""
import logging
from typing import List, Optional

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Core send helpers
# ─────────────────────────────────────────────────────────────────────────────

def _from_email() -> str:
    return getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@certify-u.com')


def _safe_send(subject: str, body: str, to: List[str]) -> bool:
    """Plain-text best-effort send (legacy / fallback)."""
    recipients = [r for r in to if r]
    if not recipients:
        return False
    try:
        send_mail(subject, body, _from_email(), recipients, fail_silently=True)
        return True
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning('Email send failed: %s', exc)
        return False


def _email_base_context() -> dict:
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'Certify-U'),
        'frontend_url': getattr(settings, 'FRONTEND_BASE_URL', 'https://certify-u.com'),
        'logo_url': getattr(settings, 'EMAIL_LOGO_URL', ''),
        'brand_color': getattr(settings, 'EMAIL_BRAND_COLOR', '#F47A20'),
        'year': timezone.now().year,
    }


def _frontend_url(path: str = '') -> str:
    base = getattr(settings, 'FRONTEND_BASE_URL', 'https://certify-u.com').rstrip('/')
    if not path:
        return base
    return base + '/' + path.lstrip('/')


def _send_template(subject: str, template: str, context: dict, to: List[str],
                   text_body: Optional[str] = None, fail_silently: bool = True) -> bool:
    """Render emails/<template> to HTML (+ text fallback) and send.

    Falls back to a plain-text send if template rendering fails. When
    ``fail_silently`` is False, send/render errors propagate to the caller.
    """
    recipients = [r for r in to if r]
    if not recipients:
        return False
    ctx = _email_base_context()
    ctx.update(context or {})
    try:
        html = render_to_string(f'emails/{template}', ctx)
    except Exception as exc:
        logger.warning('Email template render failed (%s): %s', template, exc)
        if fail_silently:
            return _safe_send(subject, text_body or subject, recipients)
        raise
    text = text_body or strip_tags(html)
    try:
        msg = EmailMultiAlternatives(subject, text, _from_email(), recipients)
        msg.attach_alternative(html, 'text/html')
        msg.send(fail_silently=fail_silently)
        return True
    except Exception as exc:
        logger.warning('HTML email send failed (%s): %s', template, exc)
        if fail_silently:
            return False
        raise


# ─────────────────────────────────────────────────────────────────────────────
# Admin notifications
# ─────────────────────────────────────────────────────────────────────────────

def _admin_recipients() -> List[str]:
    raw = (
        getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', '')
        or getattr(settings, 'DEFAULT_FROM_EMAIL', '')
        or ''
    )
    return [e.strip() for e in raw.split(',') if e.strip()]


def notify_admin(subject: str, body: str) -> bool:
    """Generic plain-text admin alert (kept for ad-hoc use)."""
    return _safe_send(f"[Certify-U Admin] {subject}", body, _admin_recipients())


def notify_admin_new_user(user) -> bool:
    role = ''
    profile = getattr(user, 'user_profile', None)
    if profile is not None:
        role = getattr(profile, 'role', '') or ''
    details = [
        ('Username', user.get_username()),
        ('Name', user.get_full_name() or '(not set)'),
        ('Email', user.email or '(not set)'),
        ('Role', role or '(default)'),
        ('User ID', user.pk),
        ('Joined', getattr(user, 'date_joined', '')),
    ]
    return _send_template(
        subject=f"[Certify-U Admin] New user registered: {user.get_username()}",
        template='admin_new_user.html',
        context={'user_name': user.get_username(), 'details': details},
        to=_admin_recipients(),
    )


def notify_admin_new_course(course) -> bool:
    try:
        instructors = ', '.join(
            i.user.get_username() for i in course.instructors.all()
        ) or '(none)'
    except Exception:
        instructors = '(unknown)'
    details = [
        ('Title', course.title),
        ('Course ID', course.pk),
        ('Instructors', instructors),
        ('Status', course.status),
        ('Approved', course.is_approved),
        ('Price', f"{course.price} {course.currency}"),
    ]
    return _send_template(
        subject=f"[Certify-U Admin] New course created: {course.title}",
        template='admin_new_course.html',
        context={'course_title': course.title, 'details': details},
        to=_admin_recipients(),
    )


def notify_admin_course_updated(course, changed_fields: List[str]) -> bool:
    details = [
        ('Title', course.title),
        ('Course ID', course.pk),
        ('Status', course.status),
        ('Approved', course.is_approved),
        ('Fields changed', ', '.join(changed_fields) or '(unspecified)'),
    ]
    return _send_template(
        subject=f"[Certify-U Admin] Course updated: {course.title}",
        template='admin_course_updated.html',
        context={'course_title': course.title, 'details': details},
        to=_admin_recipients(),
    )


def notify_admin_new_payment(enrollment) -> bool:
    """Fired on a new enrolment — the platform's current checkout/payment event."""
    student = enrollment.student
    course = enrollment.course
    try:
        is_paid = float(course.price) > 0
    except (TypeError, ValueError):
        is_paid = False
    kind = 'payment' if is_paid else 'free'
    amount = f"{course.price} {course.currency}" + ('' if is_paid else ' (free)')
    details = [
        ('Student', f"{student.get_username()} ({student.email or 'no email'})"),
        ('Course', f"{course.title} (ID {course.pk})"),
        ('Amount', amount),
        ('Enrolment ID', enrollment.pk),
    ]
    return _send_template(
        subject=f"[Certify-U Admin] New {kind} enrolment: {course.title}",
        template='admin_new_payment.html',
        context={'course_title': course.title, 'kind': kind, 'details': details},
        to=_admin_recipients(),
    )


def notify_admin_security_event(event: str, detail: str, **context) -> bool:
    details = [('Event', event), ('Detail', detail)]
    details += [(k.upper() if len(k) <= 3 else k.replace('_', ' ').title(), v)
                for k, v in context.items() if v]
    return _send_template(
        subject=f"[Certify-U Admin] Security: {event}",
        template='admin_security.html',
        context={'event': event, 'details': details},
        to=_admin_recipients(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Student notifications
# ─────────────────────────────────────────────────────────────────────────────

def _display_name(user) -> str:
    return user.get_full_name() or user.get_username()


def notify_enrollment(enrollment) -> bool:
    student = enrollment.student
    course = enrollment.course
    name = _display_name(student)
    text = (
        f"Hi {name},\n\n"
        f"You're now enrolled in '{course.title}'. Log in to start learning.\n\n"
        f"{_frontend_url('/dashboard/student-enroll-course')}\n\n— Certify-U"
    )
    return _send_template(
        subject=f"You're enrolled in {course.title}",
        template='student_enrollment.html',
        context={
            'recipient_name': name,
            'course_title': course.title,
            'cta_url': _frontend_url('/dashboard/student-enroll-course'),
            'cta_label': 'Go to my courses',
        },
        to=[student.email],
        text_body=text,
    )


def notify_booking_confirmed(booking) -> bool:
    student = booking.student
    slot = booking.slot
    name = _display_name(student)
    when = f"{slot.start_time:%d %b %Y %H:%M}"
    details = [
        ('Date & time', when),
        ('Mode', slot.get_mode_display()),
        ('Location', slot.location or 'TBC'),
    ]
    text = (
        f"Hi {name},\n\n"
        f"Your booking for '{slot.course.title}' on {when} is confirmed.\n"
        f"Mode: {slot.get_mode_display()}\nLocation: {slot.location or 'TBC'}\n\n— Certify-U"
    )
    return _send_template(
        subject=f"Booking confirmed — {slot.course.title}",
        template='student_booking_confirmed.html',
        context={
            'recipient_name': name,
            'course_title': slot.course.title,
            'details': details,
            'cta_url': _frontend_url('/dashboard'),
            'cta_label': 'View my dashboard',
        },
        to=[student.email],
        text_body=text,
    )


def notify_certificate_issued(certificate) -> bool:
    enrollment = certificate.enrollment
    student = enrollment.student
    course = enrollment.course
    name = _display_name(student)
    details = [
        ('Course', course.title),
        ('Certificate ID', certificate.certificate_id),
    ]
    text = (
        f"Hi {name},\n\n"
        f"Your certificate ({certificate.certificate_id}) for '{course.title}' "
        f"has been issued. Download it from your dashboard.\n\n"
        f"{_frontend_url('/certificate/%s' % course.pk)}\n\n— Certify-U"
    )
    return _send_template(
        subject=f"Your certificate for {course.title} is ready",
        template='student_certificate.html',
        context={
            'recipient_name': name,
            'course_title': course.title,
            'details': details,
            'cta_url': _frontend_url('/certificate/%s' % course.pk),
            'cta_label': 'Download certificate',
        },
        to=[student.email],
        text_body=text,
    )


def notify_assessment_result(attempt) -> bool:
    student = attempt.student
    assessment = attempt.assessment
    name = _display_name(student)
    score = round(attempt.score or 0)
    encouragement = (
        getattr(assessment, 'encouragement_message', '') or
        "Keep going — you can retake it."
    )
    if attempt.passed:
        text = f"Hi {name},\n\nYou passed '{assessment.title}' with a score of {score}%.\n\n— Certify-U"
    else:
        text = (
            f"Hi {name},\n\nYour score on '{assessment.title}' was {score}% "
            f"(passing: {assessment.passing_score}%).\n\n{encouragement}\n\n— Certify-U"
        )
    return _send_template(
        subject=f"Assessment result: {assessment.title}",
        template='student_assessment_result.html',
        context={
            'recipient_name': name,
            'assessment_title': assessment.title,
            'score': score,
            'passed': attempt.passed,
            'passing_score': assessment.passing_score,
            'encouragement': encouragement,
            'cta_url': _frontend_url('/dashboard/student-enroll-course'),
            'cta_label': 'Back to my courses',
        },
        to=[student.email],
        text_body=text,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Trainer notifications
# ─────────────────────────────────────────────────────────────────────────────

def notify_trainer_course_added(course, instructor) -> bool:
    user = getattr(instructor, 'user', None)
    if user is None:
        return False
    name = _display_name(user)
    is_published = (course.status == 'published') or bool(course.is_approved)
    details = [
        ('Course', course.title),
        ('Status', course.status),
        ('Price', f"{course.price} {course.currency}"),
    ]
    text = (
        f"Hi {name},\n\n"
        f"Your course '{course.title}' was successfully created on Certify-U. "
        f"Add modules, lessons and a final assessment to get it ready for learners.\n\n"
        f"{_frontend_url('/dashboard')}\n\n— Certify-U"
    )
    return _send_template(
        subject=f"Your course \"{course.title}\" was created",
        template='trainer_course_added.html',
        context={
            'recipient_name': name,
            'course_title': course.title,
            'is_published': is_published,
            'details': details,
            'cta_url': _frontend_url('/dashboard'),
            'cta_label': 'Manage my course',
        },
        to=[user.email],
        text_body=text,
    )


def notify_trainer_document_review(document) -> bool:
    """Notify the trainer that a document review state changed."""
    instructor = document.instructor
    user = instructor.user
    name = _display_name(user)
    status_label = document.get_status_display()
    doc_type = document.get_document_type_display()
    details = [
        ('Document', document.title),
        ('Type', doc_type),
        ('Status', status_label),
        ('Notes', document.review_notes or '(none)'),
    ]
    text = (
        f"Hi {name},\n\n"
        f"Your '{doc_type}' submission is now marked as {status_label}.\n"
        f"Notes: {document.review_notes or '(none)'}\n\n— Certify-U"
    )
    return _send_template(
        subject=f"Document {status_label}: {document.title}",
        template='trainer_document_review.html',
        context={
            'recipient_name': name,
            'document_title': document.title,
            'document_type': doc_type,
            'status_label': status_label,
            'details': details,
            'cta_url': _frontend_url('/dashboard'),
            'cta_label': 'View my dashboard',
        },
        to=[user.email],
        text_body=text,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Shared (students + trainers): password reset OTP
# ─────────────────────────────────────────────────────────────────────────────

def notify_password_reset_otp(email: str, otp: str, name: str = 'there',
                              ttl_minutes: int = 10,
                              subject: Optional[str] = None,
                              text_body: Optional[str] = None) -> bool:
    """Send the password-reset OTP. Errors propagate (fail_silently=False) so the
    caller keeps its existing send-failure handling."""
    subject = subject or "Your Certify-U password reset code"
    return _send_template(
        subject=subject,
        template='password_reset.html',
        context={'recipient_name': name, 'otp': otp, 'ttl_minutes': ttl_minutes},
        to=[email],
        text_body=text_body,
        fail_silently=False,
    )

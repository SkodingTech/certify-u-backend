"""Lightweight email notification helpers.

These call Django's send_mail directly. Failures are swallowed so a missing SMTP
config never blocks the request — production should wire a proper backend +
queue, but the API surface is correct.
"""
import logging
from typing import List

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _safe_send(subject: str, body: str, to: List[str]) -> bool:
    recipients = [r for r in to if r]
    if not recipients:
        return False
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@certify-u.com')
    try:
        send_mail(subject, body, from_email, recipients, fail_silently=True)
        return True
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning('Email send failed: %s', exc)
        return False


def notify_enrollment(enrollment) -> bool:
    student = enrollment.student
    return _safe_send(
        subject=f"You're enrolled in {enrollment.course.title}",
        body=(
            f"Hi {student.get_full_name() or student.username},\n\n"
            f"You're now enrolled in '{enrollment.course.title}'. "
            "Log in to start learning.\n\n— Certify-U"
        ),
        to=[student.email],
    )


def notify_booking_confirmed(booking) -> bool:
    student = booking.student
    slot = booking.slot
    return _safe_send(
        subject=f"Booking confirmed — {slot.course.title}",
        body=(
            f"Hi {student.get_full_name() or student.username},\n\n"
            f"Your booking for '{slot.course.title}' on "
            f"{slot.start_time:%d %b %Y %H:%M} is confirmed.\n"
            f"Mode: {slot.get_mode_display()}\n"
            f"Location: {slot.location or 'TBC'}\n\n— Certify-U"
        ),
        to=[student.email],
    )


def notify_certificate_issued(certificate) -> bool:
    enrollment = certificate.enrollment
    student = enrollment.student
    return _safe_send(
        subject=f"Your certificate for {enrollment.course.title} is ready",
        body=(
            f"Hi {student.get_full_name() or student.username},\n\n"
            f"Your certificate ({certificate.certificate_id}) for "
            f"'{enrollment.course.title}' has been issued. "
            "Download it from your dashboard.\n\n— Certify-U"
        ),
        to=[student.email],
    )


def notify_trainer_document_review(document) -> bool:
    """Notify the trainer that a document review state changed."""
    instructor = document.instructor
    user = instructor.user
    status_label = document.get_status_display()
    return _safe_send(
        subject=f"Document {status_label}: {document.title}",
        body=(
            f"Hi {user.get_full_name() or user.username},\n\n"
            f"Your '{document.get_document_type_display()}' submission is now "
            f"marked as {status_label}.\n"
            f"Notes: {document.review_notes or '(none)'}\n\n— Certify-U"
        ),
        to=[user.email],
    )


def notify_assessment_result(attempt) -> bool:
    student = attempt.student
    assessment = attempt.assessment
    if attempt.passed:
        body = (
            f"Hi {student.get_full_name() or student.username},\n\n"
            f"You passed '{assessment.title}' with a score of {attempt.score:.0f}%.\n\n— Certify-U"
        )
    else:
        encouragement = assessment.encouragement_message or "Keep going — you can retake it."
        body = (
            f"Hi {student.get_full_name() or student.username},\n\n"
            f"Your score on '{assessment.title}' was {attempt.score:.0f}% "
            f"(passing: {assessment.passing_score}%).\n\n{encouragement}\n\n— Certify-U"
        )
    return _safe_send(
        subject=f"Assessment result: {assessment.title}",
        body=body,
        to=[student.email],
    )

"""Endpoints for: bookings, slots, trainer availability, trainer/student documents,
job roles, certificates, support, schedule aggregation, instructor public profile,
offline attendance check-in/out.
"""
from datetime import datetime

from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import generics, pagination, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import (
    Booking,
    Certificate,
    Enrollment,
    Instructor,
    JobRole,
    LiveSession,
    SessionAttendance,
    Slot,
    StudentDocument,
    SupportChannel,
    SupportTicket,
    TrainerAvailability,
    TrainerDocument,
)
from courses.models.assessment import AssessmentAttempt
from courses.serializers import (
    BookingSerializer,
    CertificateSerializer,
    InstructorPublicProfileSerializer,
    InstructorVerificationSerializer,
    JobRoleSerializer,
    SlotSerializer,
    StudentDocumentReviewSerializer,
    StudentDocumentSerializer,
    SupportChannelSerializer,
    SupportTicketSerializer,
    TrainerAvailabilitySerializer,
    TrainerDocumentReviewSerializer,
    TrainerDocumentSerializer,
)
from courses.services.certificate_pdf import issue_certificate
from courses.services import notifications


class DefaultPagination(pagination.PageNumberPagination):
    page_size = 25


def _get_instructor(user):
    if hasattr(user, 'instructor'):
        return user.instructor
    return Instructor.objects.filter(user=user).first()


def _is_admin(user):
    """Caller is platform admin: Django staff/superuser or profile role ADMIN/SUPER_ADMIN."""
    if not (user and user.is_authenticated):
        return False
    if user.is_staff or user.is_superuser:
        return True
    prof = getattr(user, 'user_profile', None) or getattr(user, 'userprofile', None)
    return bool(prof and getattr(prof, 'role', None) in ('ADMIN', 'SUPER_ADMIN'))


# ──────────────────────────────────────────────────────────────────────────────
# Trainer Availability
# ──────────────────────────────────────────────────────────────────────────────
class TrainerAvailabilityListCreateView(generics.ListCreateAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = TrainerAvailabilitySerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        instructor_id = self.request.query_params.get('instructor_id')
        qs = TrainerAvailability.objects.all()
        if instructor_id:
            qs = qs.filter(instructor_id=instructor_id)
        elif _is_admin(self.request.user):
            pass  # admin sees all
        else:
            inst = _get_instructor(self.request.user)
            qs = qs.filter(instructor=inst) if inst else qs.none()
        return qs

    def perform_create(self, serializer):
        inst = _get_instructor(self.request.user)
        if not inst:
            raise permissions.exceptions.PermissionDenied("Only instructors can set availability.")
        serializer.save(instructor=inst)


class TrainerAvailabilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = TrainerAvailabilitySerializer
    queryset = TrainerAvailability.objects.all()


# ──────────────────────────────────────────────────────────────────────────────
# Slots
# ──────────────────────────────────────────────────────────────────────────────
class SlotListCreateView(generics.ListCreateAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = SlotSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        qs = Slot.objects.filter(is_deleted=False)
        course_id = self.request.query_params.get('course_id')
        instructor_id = self.request.query_params.get('instructor_id')
        mode = self.request.query_params.get('mode')
        upcoming = self.request.query_params.get('upcoming')
        if course_id:
            qs = qs.filter(course_id=course_id)
        if instructor_id:
            qs = qs.filter(instructor_id=instructor_id)
        if mode:
            qs = qs.filter(mode=mode)
        if upcoming in ('1', 'true', 'yes'):
            qs = qs.filter(start_time__gte=timezone.now())
        return qs

    def perform_create(self, serializer):
        inst = _get_instructor(self.request.user)
        if not inst:
            raise permissions.exceptions.PermissionDenied("Only instructors can create slots.")
        serializer.save(instructor=inst)


class SlotDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = SlotSerializer
    queryset = Slot.objects.all()


# ──────────────────────────────────────────────────────────────────────────────
# Bookings
# ──────────────────────────────────────────────────────────────────────────────
class BookingListCreateView(generics.ListCreateAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = BookingSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        user = self.request.user
        qs = Booking.objects.all()
        if _is_admin(user):
            return qs  # admin sees every booking
        inst = _get_instructor(user)
        if inst and self.request.query_params.get('as') == 'instructor':
            return qs.filter(slot__instructor=inst)
        return qs.filter(student=user)

    def create(self, request, *args, **kwargs):
        slot_id = request.data.get('slot')
        if not slot_id:
            return Response({'error': 'slot is required'}, status=status.HTTP_400_BAD_REQUEST)
        slot = get_object_or_404(Slot, pk=slot_id)

        # Hybrid gating: if course is hybrid and has an assessment, require a passing attempt
        course = slot.course
        if course.delivery_mode == 'hybrid' and slot.mode == 'offline':
            if hasattr(course, 'assessment'):
                passed = AssessmentAttempt.objects.filter(
                    student=request.user, assessment=course.assessment, passed=True
                ).exists()
                if not passed:
                    return Response(
                        {'error': 'You must pass the theory assessment before booking the offline practical slot.'},
                        status=status.HTTP_403_FORBIDDEN,
                    )

        if slot.status != 'open':
            return Response({'error': f'Slot is {slot.status}.'}, status=status.HTTP_400_BAD_REQUEST)

        if slot.seats_remaining <= 0:
            return Response({'error': 'No seats remaining.'}, status=status.HTTP_400_BAD_REQUEST)

        booking, created = Booking.objects.get_or_create(
            slot=slot, student=request.user,
            defaults={'status': 'confirmed'},
        )
        if not created and booking.status == 'cancelled':
            booking.status = 'confirmed'
            booking.cancelled_at = None
            booking.save()

        if created:
            slot.seats_taken = min(slot.seats_taken + 1, slot.capacity)
            if slot.seats_remaining == 0:
                slot.status = 'full'
            slot.save()
            notifications.notify_booking_confirmed(booking)

        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class BookingCancelView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk, *args, **kwargs):
        booking = get_object_or_404(Booking, pk=pk)
        if booking.student != request.user and not request.user.is_staff:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        if booking.status == 'cancelled':
            return Response({'status': 'already_cancelled'})

        reason = request.data.get('reason', '')
        booking.status = 'cancelled'
        booking.cancelled_at = timezone.now()
        booking.cancellation_reason = reason
        booking.save()

        slot = booking.slot
        slot.seats_taken = max(slot.seats_taken - 1, 0)
        if slot.status == 'full':
            slot.status = 'open'
        slot.save()
        return Response({'status': 'cancelled'})


# ──────────────────────────────────────────────────────────────────────────────
# Trainer Documents (onboarding & verification)
# ──────────────────────────────────────────────────────────────────────────────
class TrainerDocumentListCreateView(generics.ListCreateAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = TrainerDocumentSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            qs = TrainerDocument.objects.all()
        else:
            inst = _get_instructor(user)
            qs = TrainerDocument.objects.filter(instructor=inst) if inst else TrainerDocument.objects.none()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        inst = _get_instructor(self.request.user)
        if not inst:
            raise permissions.exceptions.PermissionDenied("Only instructors can upload documents.")
        doc = serializer.save(instructor=inst, status='pending')
        # Move instructor into pending review state
        if inst.verification_status in ('unsubmitted', 'rejected', 'resubmit'):
            inst.verification_status = 'pending'
            inst.save(update_fields=['verification_status'])
        return doc


class TrainerDocumentReviewView(APIView):
    """Admin endpoint to approve/reject/request resubmission of a trainer document."""
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk, *args, **kwargs):
        if not request.user.is_staff:
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        document = get_object_or_404(TrainerDocument, pk=pk)
        serializer = TrainerDocumentReviewSerializer(document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        document = serializer.save(reviewed_by=request.user, reviewed_at=timezone.now())

        # Bubble status up to instructor record
        inst = document.instructor
        all_docs = inst.documents.all()
        if all_docs.filter(status='approved').count() and not all_docs.exclude(status__in=['approved']).exists():
            inst.verification_status = 'approved'
            inst.verified = True
        elif all_docs.filter(status='rejected').exists():
            inst.verification_status = 'rejected'
            inst.verified = False
        elif all_docs.filter(status='resubmit').exists():
            inst.verification_status = 'resubmit'
        inst.save()

        notifications.notify_trainer_document_review(document)
        return Response(TrainerDocumentSerializer(document).data)


class InstructorVerificationStatusView(APIView):
    """Admin endpoint to set overall instructor verification status."""
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk, *args, **kwargs):
        if not request.user.is_staff:
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        instructor = get_object_or_404(Instructor, pk=pk)
        serializer = InstructorVerificationSerializer(instructor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ──────────────────────────────────────────────────────────────────────────────
# Student Documents
# ──────────────────────────────────────────────────────────────────────────────
class StudentDocumentListCreateView(generics.ListCreateAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = StudentDocumentSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            qs = StudentDocument.objects.all()
            student_id = self.request.query_params.get('student_id')
            if student_id:
                qs = qs.filter(student_id=student_id)
            return qs
        return StudentDocument.objects.filter(student=user)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user, status='pending')


class StudentDocumentReviewView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk, *args, **kwargs):
        if not request.user.is_staff:
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        document = get_object_or_404(StudentDocument, pk=pk)
        serializer = StudentDocumentReviewSerializer(document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(reviewed_by=request.user, reviewed_at=timezone.now())
        return Response(StudentDocumentSerializer(document).data)


# ──────────────────────────────────────────────────────────────────────────────
# Job Roles
# ──────────────────────────────────────────────────────────────────────────────
class JobRoleListCreateView(generics.ListCreateAPIView):
    authentication_classes = (OAuth2Authentication,)
    serializer_class = JobRoleSerializer
    pagination_class = DefaultPagination

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = JobRole.objects.filter(is_deleted=False)
        course_id = self.request.query_params.get('course_id')
        if course_id:
            qs = qs.filter(courses__id=course_id)
        return qs.distinct()


class JobRoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = JobRoleSerializer
    queryset = JobRole.objects.all()


# ──────────────────────────────────────────────────────────────────────────────
# Certificate issuance & download
# ──────────────────────────────────────────────────────────────────────────────
def _student_compliance_ok(student, course):
    """Compliance gate — when course requires it, all student docs must be approved."""
    if not course.require_student_compliance:
        return True
    docs = StudentDocument.objects.filter(student=student)
    if not docs.exists():
        return False
    return not docs.exclude(status='approved').exists()


class CertificateIssueView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, enrollment_id, *args, **kwargs):
        enrollment = get_object_or_404(Enrollment, pk=enrollment_id)
        # Only the student themselves, the course instructor, or admin
        is_owner = enrollment.student == request.user
        is_instructor_for_course = enrollment.course.instructors.filter(user=request.user).exists()
        if not (is_owner or is_instructor_for_course or request.user.is_staff):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        if enrollment.status != 'completed' and enrollment.progress < 100:
            return Response({'error': 'Course not completed.'}, status=status.HTTP_400_BAD_REQUEST)

        if not _student_compliance_ok(enrollment.student, enrollment.course):
            return Response(
                {'error': 'Student compliance documents pending — certificate cannot be issued yet.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        certificate = issue_certificate(enrollment)
        notifications.notify_certificate_issued(certificate)
        return Response(CertificateSerializer(certificate).data, status=status.HTTP_201_CREATED)


class CertificateDownloadView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, certificate_id, *args, **kwargs):
        certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
        if certificate.is_revoked:
            return Response({'error': 'Certificate has been revoked.'}, status=status.HTTP_410_GONE)
        if not certificate.pdf_file:
            return Response({'error': 'Certificate PDF not generated yet.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            return FileResponse(certificate.pdf_file.open('rb'), content_type='application/pdf')
        except FileNotFoundError:
            raise Http404


class MyCertificatesView(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CertificateSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        return Certificate.objects.filter(enrollment__student=self.request.user).order_by('-issued_at')


class CertificateAdminListView(generics.ListAPIView):
    """Admin/instructor view of all certificates."""
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CertificateSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Certificate.objects.all().order_by('-issued_at')
        inst = _get_instructor(user)
        if inst:
            return Certificate.objects.filter(enrollment__course__instructors=inst).order_by('-issued_at')
        return Certificate.objects.none()


# ──────────────────────────────────────────────────────────────────────────────
# Schedule aggregation
# ──────────────────────────────────────────────────────────────────────────────
class ScheduleView(APIView):
    """Unified schedule for a learner or instructor: bookings + live sessions + slots."""
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        role = request.query_params.get('as', 'student')
        events = []

        def _push(kind, when_start, when_end, title, ref_id, extra=None):
            events.append({
                'kind': kind,
                'start': when_start,
                'end': when_end,
                'title': title,
                'id': ref_id,
                **(extra or {}),
            })

        if role == 'instructor':
            inst = _get_instructor(user)
            if not inst:
                return Response([], status=200)
            for slot in Slot.objects.filter(instructor=inst, is_deleted=False).order_by('start_time'):
                _push('slot', slot.start_time, slot.end_time, f"{slot.course.title} ({slot.get_mode_display()})", slot.id, {'mode': slot.mode, 'status': slot.status})
            for ls in LiveSession.objects.filter(instructor=inst).order_by('start_time'):
                _push('live_session', ls.start_time, ls.end_time, ls.title, ls.id, {'status': ls.status})
        else:
            for booking in Booking.objects.filter(student=user).exclude(status='cancelled').order_by('slot__start_time'):
                slot = booking.slot
                _push('booking', slot.start_time, slot.end_time, slot.course.title, booking.id, {'status': booking.status, 'mode': slot.mode})
            for ls in LiveSession.objects.filter(attendees=user).order_by('start_time'):
                _push('live_session', ls.start_time, ls.end_time, ls.title, ls.id, {'status': ls.status})

        return Response(events)


# ──────────────────────────────────────────────────────────────────────────────
# Offline attendance check-in / out
# ──────────────────────────────────────────────────────────────────────────────
class SlotCheckInView(APIView):
    """Mark a learner present at an offline slot. Instructors can mark on a learner's behalf."""
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, slot_id, *args, **kwargs):
        slot = get_object_or_404(Slot, pk=slot_id)
        student_id = request.data.get('student_id')
        if student_id and student_id != request.user.id:
            inst = _get_instructor(request.user)
            if not (inst and slot.instructor_id == inst.id) and not request.user.is_staff:
                return Response({'error': 'Only the slot instructor or admin can mark attendance for others.'}, status=status.HTTP_403_FORBIDDEN)
            from django.contrib.auth import get_user_model
            student = get_object_or_404(get_user_model(), pk=student_id)
            marked_by_instructor = True
        else:
            student = request.user
            marked_by_instructor = False

        attendance, _ = SessionAttendance.objects.get_or_create(slot=slot, student=student)
        attendance.check_in_time = attendance.check_in_time or timezone.now()
        attendance.is_present = True
        attendance.marked_by_instructor = marked_by_instructor
        attendance.save()
        return Response({'status': 'checked_in', 'check_in_time': attendance.check_in_time})


class SlotCheckOutView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, slot_id, *args, **kwargs):
        slot = get_object_or_404(Slot, pk=slot_id)
        attendance = SessionAttendance.objects.filter(slot=slot, student=request.user).first()
        if not attendance or not attendance.check_in_time:
            return Response({'error': 'No active check-in.'}, status=status.HTTP_400_BAD_REQUEST)
        attendance.check_out_time = timezone.now()
        attendance.save()
        return Response({'status': 'checked_out', 'check_out_time': attendance.check_out_time})


class SlotAttendanceListView(generics.ListAPIView):
    """List attendance records for a slot — instructor / admin only."""
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def list(self, request, slot_id, *args, **kwargs):
        slot = get_object_or_404(Slot, pk=slot_id)
        inst = _get_instructor(request.user)
        if not request.user.is_staff and not (inst and slot.instructor_id == inst.id):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        records = SessionAttendance.objects.filter(slot=slot).select_related('student')
        data = [
            {
                'student_id': r.student_id,
                'student_name': r.student.get_full_name() or r.student.username,
                'check_in_time': r.check_in_time,
                'check_out_time': r.check_out_time,
                'is_present': r.is_present,
                'marked_by_instructor': r.marked_by_instructor,
            }
            for r in records
        ]
        return Response(data)


# ──────────────────────────────────────────────────────────────────────────────
# Instructor public profile
# ──────────────────────────────────────────────────────────────────────────────
class InstructorPublicProfileView(generics.RetrieveAPIView):
    serializer_class = InstructorPublicProfileSerializer
    queryset = Instructor.objects.all()
    permission_classes = (permissions.AllowAny,)


# ──────────────────────────────────────────────────────────────────────────────
# Support: channels + tickets + WhatsApp webhook stub
# ──────────────────────────────────────────────────────────────────────────────
class SupportChannelListView(generics.ListAPIView):
    """Public list of support contact channels."""
    serializer_class = SupportChannelSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        return SupportChannel.objects.filter(is_published=True, is_deleted=False)


class SupportTicketListCreateView(generics.ListCreateAPIView):
    serializer_class = SupportTicketSerializer
    pagination_class = DefaultPagination

    def get_authenticators(self):
        if self.request and self.request.method == 'POST':
            return [OAuth2Authentication()]
        return [OAuth2Authentication()]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return SupportTicket.objects.all()
        if user.is_authenticated:
            return SupportTicket.objects.filter(user=user)
        return SupportTicket.objects.none()

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user, source=self.request.data.get('source', 'web'))


class SupportTicketUpdateView(generics.UpdateAPIView):
    """Admin endpoint to update ticket status / assignee."""
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = SupportTicketSerializer
    queryset = SupportTicket.objects.all()

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise permissions.exceptions.PermissionDenied("Admin only.")
        new_status = self.request.data.get('status')
        if new_status == 'resolved':
            serializer.save(resolved_at=timezone.now())
        else:
            serializer.save()


class WhatsAppWebhookView(APIView):
    """Inbound WhatsApp messages → SupportTicket. Provider-agnostic stub.

    Configure your provider (Twilio / 360dialog / Meta Cloud API) to POST inbound
    messages here. The handler captures them as tickets so support staff can reply.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        # Best-effort field extraction across providers.
        body = request.data
        contact = body.get('From') or body.get('from') or body.get('wa_id') or ''
        message = body.get('Body') or body.get('text') or body.get('message') or ''
        name = body.get('ProfileName') or body.get('name') or ''
        if not message and not contact:
            return Response({'status': 'ignored'}, status=status.HTTP_200_OK)

        SupportTicket.objects.create(
            contact=contact,
            name=name,
            source='whatsapp',
            message=message,
            subject=(message[:50] + '…') if len(message) > 50 else message,
        )
        return Response({'status': 'received'}, status=status.HTTP_200_OK)

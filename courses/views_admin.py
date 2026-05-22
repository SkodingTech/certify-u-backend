"""Admin/CMS CRUD endpoints for courses-app models not yet exposed by the
main views.py or views_extra.py.

All endpoints are open to authenticated users; permission gating can be tightened
later via IsAdmin / IsSuperAdmin from users.permissions.
"""
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import generics, pagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsCMSAdmin

from courses.models import (
    AssessmentAttempt,
    ComplianceDocument,
    Discussion,
    DiscussionReply,
    Instructor,
    LessonProgress,
    LiveSessionRequest,
    ModuleProgress,
    Organization,
    PresentationProgress,
    RegulatoryAuthority,
    RegulatoryCompliance,
    RegulatoryReference,
    Review,
    StudentDocument,
    SupportChannel,
    TrainerAvailability,
)
from courses.serializers import (
    AssessmentAttemptAdminSerializer,
    ComplianceDocumentSerializer,
    DiscussionReplySerializer,
    DiscussionSerializer,
    InstructorSerializer,
    LessonProgressSerializer,
    LiveSessionRequestAdminSerializer,
    ModuleProgressSerializer,
    OrganizationSerializer,
    PresentationProgressSerializer,
    RegulatoryAuthoritySerializer,
    RegulatoryComplianceSerializer,
    RegulatoryReferenceSerializer,
    ReviewAdminSerializer,
    StudentDocumentSerializer,
    SupportChannelSerializer,
    TrainerAvailabilitySerializer,
)


class AdminPagination(pagination.PageNumberPagination):
    page_size = 25


class _BaseLC(generics.ListCreateAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    parser_classes = (MultiPartParser, FormParser, JSONParser)


class _BaseDET(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    parser_classes = (MultiPartParser, FormParser, JSONParser)


# ── Organization ─────────────────────────────────────────────────────────────
class OrganizationListCreate(_BaseLC):
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.filter(is_deleted=False).order_by('-id')


class OrganizationDetail(_BaseDET):
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()


# ── Instructor admin list ────────────────────────────────────────────────────
class InstructorAdminList(_BaseLC):
    serializer_class = InstructorSerializer
    queryset = Instructor.objects.filter(is_deleted=False).order_by('-id')


class InstructorAdminDetail(_BaseDET):
    serializer_class = InstructorSerializer
    queryset = Instructor.objects.all()


# ── TrainerAvailability admin (cross-instructor) ─────────────────────────────
class TrainerAvailabilityAdminList(_BaseLC):
    serializer_class = TrainerAvailabilitySerializer
    queryset = TrainerAvailability.objects.all().order_by('-id')


class TrainerAvailabilityAdminDetail(_BaseDET):
    serializer_class = TrainerAvailabilitySerializer
    queryset = TrainerAvailability.objects.all()


# ── Reviews ──────────────────────────────────────────────────────────────────
class ReviewAdminList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    serializer_class = ReviewAdminSerializer

    def get_queryset(self):
        qs = Review.objects.filter(is_deleted=False).order_by('-id')
        course_id = self.request.query_params.get('course_id')
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs


class ReviewAdminDetail(generics.RetrieveDestroyAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    serializer_class = ReviewAdminSerializer
    queryset = Review.objects.all()


# ── AssessmentAttempt admin ──────────────────────────────────────────────────
class AssessmentAttemptAdminList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    serializer_class = AssessmentAttemptAdminSerializer

    def get_queryset(self):
        qs = AssessmentAttempt.objects.all().order_by('-id')
        passed = self.request.query_params.get('passed')
        if passed in ('1', 'true', 'false', '0'):
            qs = qs.filter(passed=passed in ('1', 'true'))
        return qs


class AssessmentAttemptAdminDetail(generics.RetrieveAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    serializer_class = AssessmentAttemptAdminSerializer
    queryset = AssessmentAttempt.objects.all()


# ── Progress admin lists ─────────────────────────────────────────────────────
class LessonProgressAdminList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    serializer_class = LessonProgressSerializer
    queryset = LessonProgress.objects.all().order_by('-id')


class ModuleProgressAdminList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    serializer_class = ModuleProgressSerializer
    queryset = ModuleProgress.objects.all().order_by('-id')


class PresentationProgressAdminList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    serializer_class = PresentationProgressSerializer
    queryset = PresentationProgress.objects.all().order_by('-id')


# ── LiveSessionRequest admin list ────────────────────────────────────────────
class LiveSessionRequestAdminList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    serializer_class = LiveSessionRequestAdminSerializer
    queryset = LiveSessionRequest.objects.all().order_by('-id')


# ── Discussions admin ────────────────────────────────────────────────────────
class DiscussionAdminList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    serializer_class = DiscussionSerializer
    queryset = Discussion.objects.all().order_by('-id')


class DiscussionReplyAdminList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    serializer_class = DiscussionReplySerializer
    queryset = DiscussionReply.objects.all().order_by('-id')


# ── Regulatory ───────────────────────────────────────────────────────────────
class RegulatoryAuthorityListCreate(_BaseLC):
    serializer_class = RegulatoryAuthoritySerializer
    queryset = RegulatoryAuthority.objects.filter(is_deleted=False).order_by('-id')


class RegulatoryAuthorityDetail(_BaseDET):
    serializer_class = RegulatoryAuthoritySerializer
    queryset = RegulatoryAuthority.objects.all()


class RegulatoryComplianceListCreate(_BaseLC):
    serializer_class = RegulatoryComplianceSerializer
    queryset = RegulatoryCompliance.objects.filter(is_deleted=False).order_by('-id')


class RegulatoryComplianceDetail(_BaseDET):
    serializer_class = RegulatoryComplianceSerializer
    queryset = RegulatoryCompliance.objects.all()


class RegulatoryReferenceListCreate(_BaseLC):
    serializer_class = RegulatoryReferenceSerializer
    queryset = RegulatoryReference.objects.filter(is_deleted=False).order_by('-id')


class RegulatoryReferenceDetail(_BaseDET):
    serializer_class = RegulatoryReferenceSerializer
    queryset = RegulatoryReference.objects.all()


# ── ComplianceDocument ───────────────────────────────────────────────────────
class ComplianceDocumentListCreate(_BaseLC):
    serializer_class = ComplianceDocumentSerializer
    queryset = ComplianceDocument.objects.filter(is_deleted=False).order_by('-id')


class ComplianceDocumentDetail(_BaseDET):
    serializer_class = ComplianceDocumentSerializer
    queryset = ComplianceDocument.objects.all()


# ── StudentDocument admin (read all + detail/delete) ─────────────────────────
class StudentDocumentAdminList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    serializer_class = StudentDocumentSerializer
    queryset = StudentDocument.objects.all().order_by('-id')


class StudentDocumentAdminDetail(generics.RetrieveDestroyAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    serializer_class = StudentDocumentSerializer
    queryset = StudentDocument.objects.all()


# ── SupportChannel CRUD ──────────────────────────────────────────────────────
class SupportChannelListCreate(_BaseLC):
    serializer_class = SupportChannelSerializer
    queryset = SupportChannel.objects.filter(is_deleted=False).order_by('id')


class SupportChannelDetail(_BaseDET):
    serializer_class = SupportChannelSerializer
    queryset = SupportChannel.objects.all()

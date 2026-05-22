"""SCORM admin/CMS list endpoints — modules, SCOs, runtime data, attempts."""
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import generics, pagination
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsCMSAdmin

from scorm.models import (
    ScormAttempt, ScormModule, ScormRuntimeData, ScormSco, ScormTracking,
)
from scorm.serializers import (
    ScormAttemptSerializer, ScormModuleSerializer,
    ScormRuntimeDataSerializer, ScormScoSerializer,
    ScormTrackingSerializer,
)


class AdminPagination(pagination.PageNumberPagination):
    page_size = 25


class ScormModuleAdminList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    serializer_class = ScormModuleSerializer

    def get_queryset(self):
        qs = ScormModule.objects.all().order_by('-id')
        package_id = self.request.query_params.get('package_id')
        if package_id:
            qs = qs.filter(package_id=package_id)
        return qs


class ScormScoAdminList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    serializer_class = ScormScoSerializer

    def get_queryset(self):
        qs = ScormSco.objects.all().order_by('-id')
        package_id = self.request.query_params.get('package_id')
        if package_id:
            qs = qs.filter(package_id=package_id)
        return qs


class ScormRuntimeDataAdminList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    serializer_class = ScormRuntimeDataSerializer

    def get_queryset(self):
        qs = ScormRuntimeData.objects.all().order_by('-id')
        tracking_id = self.request.query_params.get('tracking_id')
        if tracking_id:
            qs = qs.filter(tracking_id=tracking_id)
        return qs


class ScormTrackingAdminList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    serializer_class = ScormTrackingSerializer
    queryset = ScormTracking.objects.all().order_by('-id')


class ScormAttemptAdminList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    serializer_class = ScormAttemptSerializer
    queryset = ScormAttempt.objects.all().order_by('-id')

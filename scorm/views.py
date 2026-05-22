"""
SCORM API Views
Implements all SCORM endpoints for player and admin
"""
import uuid
import json
import logging

from rest_framework import status, viewsets, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from scorm.models import (
    ScormPackage, ScormTracking, ScormRuntimeData,
    ScormSco, ScormModule, ScormAttempt
)
from scorm.serializers import (
    ScormPackageSerializer, ScormPackageListSerializer,
    ScormPackageUploadSerializer, ScormTrackingSerializer,
    ScormTrackingDetailSerializer, ScormRuntimeDataSerializer,
    ScormAttemptSerializer, ScormInitSerializer,
    ScormSetValueSerializer, ScormGetValueSerializer,
    ScormCommitSerializer, ScormFinishSerializer
)
from scorm.services import ScormRuntimeEngine

logger = logging.getLogger(__name__)


class IsAuthenticated(permissions.IsAuthenticated):
    """Override default permission for SCORM"""
    pass


class IsAdminUser(permissions.BasePermission):
    """Check if user is admin. Guards against AnonymousUser (no userprofile)."""
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_staff or user.is_superuser:
            return True
        prof = getattr(user, 'user_profile', None) or getattr(user, 'userprofile', None)
        return bool(prof and getattr(prof, 'role', None) in ('ADMIN', 'SUPER_ADMIN'))


class ScormPackageViewSet(viewsets.ModelViewSet):
    """
    SCORM Package management
    CRUD operations for SCORM packages
    """
    queryset = ScormPackage.objects.filter(
        is_deleted=False
    ).select_related().prefetch_related('modules', 'scos')
    serializer_class = ScormPackageSerializer
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAdminUser,)
    parser_classes = (MultiPartParser, FormParser)

    def get_serializer_class(self):
        if self.action == 'list':
            return ScormPackageListSerializer
        elif self.action == 'create':
            return ScormPackageUploadSerializer
        return ScormPackageSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Filter by version
        version = self.request.query_params.get('version')
        if version:
            qs = qs.filter(version=version)

        return qs.order_by('-created_at')

    @action(detail=True, methods=['get'])
    def structure(self, request, pk=None):
        """Get package structure (hierarchy of modules/SCOs)"""
        package = self.get_object()
        return Response({
            'structure': package.structure_tree,
            'entry_point': package.entry_point,
            'modules': package.total_modules,
            'scos': package.total_scos,
        })

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get package analytics"""
        package = self.get_object()

        total_attempts = ScormTracking.objects.filter(
            package=package
        ).count()

        completed = ScormTracking.objects.filter(
            package=package,
            lesson_status__in=['completed', 'passed']
        ).count()

        avg_score = ScormTracking.objects.filter(
            package=package,
            score_raw__isnull=False
        ).values_list('score_raw', flat=True).aggregate(
            avg=models.Avg('score_raw')
        )

        return Response({
            'total_attempts': total_attempts,
            'completed_attempts': completed,
            'completion_rate': round((completed / total_attempts * 100), 2) if total_attempts > 0 else 0,
            'average_score': round(float(avg_score.get('avg') or 0), 2),
            'statistics': package.manifest_data.get('statistics', {}),
        })

    @action(detail=False, methods=['get'])
    def my_packages(self, request):
        """Get packages available for current user (learner)"""
        # Show all active packages to learners
        packages = ScormPackage.objects.filter(
            is_active=True,
            is_deleted=False,
            status='ready'
        )
        serializer = ScormPackageListSerializer(packages, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Create package (handled by serializer with async task)"""
        serializer.save()


class ScormInitializeView(APIView):
    """
    Initialize SCORM session
    POST /api/scorm/init/
    """
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """Initialize SCORM package for user"""
        serializer = ScormInitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        package_id = serializer.validated_data['package_id']
        sco_id = serializer.validated_data.get('sco_id')

        try:
            package = ScormPackage.objects.get(id=package_id, is_deleted=False)

            # Check if package is ready
            if package.status != 'ready':
                return Response(
                    {'error': f'Package status is {package.status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get or create tracking record
            sco = None
            if sco_id:
                sco = ScormSco.objects.get(id=sco_id, package=package)

            # Check for existing session (resume)
            existing = ScormTracking.objects.filter(
                user=request.user,
                package=package,
                sco=sco,
                lesson_status__in=['incomplete', 'browsed']
            ).first()

            if existing:
                # Resume existing session
                session_id = existing.session_id
                entry_status = 'resume'
                tracking = existing
            else:
                # New session
                session_id = str(uuid.uuid4())
                entry_status = 'ab-initio'
                tracking = ScormTracking.objects.create(
                    user=request.user,
                    package=package,
                    sco=sco,
                    session_id=session_id,
                    entry_status=entry_status,
                    ip_address=self._get_client_ip(request),
                    attempt_number=1,
                )

            # Initialize runtime engine
            version = package.version if package.version != 'unknown' else '1.2'
            engine = ScormRuntimeEngine(version)
            engine.initialize(tracking)

            return Response({
                'session_id': session_id,
                'entry_status': entry_status,
                'entry_point': package.entry_point,
                'launch_data': tracking.launch_data or {},
                'suspend_data': tracking.suspend_data or '{}',
                'version': version,
            })

        except ScormPackage.DoesNotExist:
            return Response(
                {'error': 'Package not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Initialize error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def _get_client_ip(request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ScormSetValueView(APIView):
    """
    Set SCORM CMI value
    POST /api/scorm/set-value/
    """
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """Set CMI element value"""
        serializer = ScormSetValueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data['session_id']
        element = serializer.validated_data['element']
        value = serializer.validated_data['value']

        try:
            tracking = ScormTracking.objects.get(
                session_id=session_id,
                user=request.user
            )

            # Check session validity
            if (timezone.now() - tracking.last_access).total_seconds() > 3600:
                return Response(
                    {'error': 'Session expired'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Initialize engine with package version
            version = tracking.package.version if tracking.package.version != 'unknown' else '1.2'
            engine = ScormRuntimeEngine(version)

            # Set value
            result = engine.set_value(tracking, element, value)

            if result['error_code'] != '0':
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

            return Response(result)

        except ScormTracking.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"SetValue error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ScormGetValueView(APIView):
    """
    Get SCORM CMI value
    POST /api/scorm/get-value/
    """
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """Get CMI element value"""
        serializer = ScormGetValueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data['session_id']
        element = serializer.validated_data['element']

        try:
            tracking = ScormTracking.objects.get(
                session_id=session_id,
                user=request.user
            )

            # Initialize engine
            version = tracking.package.version if tracking.package.version != 'unknown' else '1.2'
            engine = ScormRuntimeEngine(version)

            # Get value
            result = engine.get_value(tracking, element)
            return Response(result)

        except ScormTracking.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"GetValue error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ScormCommitView(APIView):
    """
    Commit SCORM data
    POST /api/scorm/commit/
    """
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """Commit CMI data"""
        serializer = ScormCommitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data['session_id']

        try:
            tracking = ScormTracking.objects.get(
                session_id=session_id,
                user=request.user
            )

            version = tracking.package.version if tracking.package.version != 'unknown' else '1.2'
            engine = ScormRuntimeEngine(version)

            result = engine.commit(tracking)
            return Response(result)

        except ScormTracking.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Commit error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ScormFinishView(APIView):
    """
    Finish SCORM session
    POST /api/scorm/finish/
    """
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """Finish SCORM session"""
        serializer = ScormFinishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data['session_id']

        try:
            tracking = ScormTracking.objects.get(
                session_id=session_id,
                user=request.user
            )

            version = tracking.package.version if tracking.package.version != 'unknown' else '1.2'
            engine = ScormRuntimeEngine(version)

            result = engine.finish(tracking)

            # Create attempt record
            ScormAttempt.objects.create(
                user=request.user,
                package=tracking.package,
                attempt_number=tracking.attempt_number,
                completion_status='completed' if tracking.lesson_status == 'completed' else 'incomplete',
                success_status='passed' if tracking.is_passed else 'failed',
                score_scaled=tracking.score_scaled,
                session_id=session_id,
            )

            return Response(result)

        except ScormTracking.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Finish error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ScormTrackingListView(generics.ListAPIView):
    """
    List SCORM tracking records for current user
    """
    serializer_class = ScormTrackingSerializer
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return ScormTracking.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('package', 'sco', 'user').order_by('-last_access')


class ScormTrackingDetailView(generics.RetrieveAPIView):
    """
    Get detailed tracking record
    """
    serializer_class = ScormTrackingDetailSerializer
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    lookup_field = 'session_id'

    def get_queryset(self):
        return ScormTracking.objects.filter(
            user=self.request.user,
            is_deleted=False
        )


class ScormAttemptListView(generics.ListAPIView):
    """
    List all attempts for current user
    """
    serializer_class = ScormAttemptSerializer
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return ScormAttempt.objects.filter(
            user=self.request.user
        ).order_by('-start_time')

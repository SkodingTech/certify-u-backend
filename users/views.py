from rest_framework.views import APIView
from django.http import HttpResponse
from rest_framework.permissions import ( IsAuthenticated,)
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from users.serializers import UserLoginSerializer
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth.models import User
from rest_framework import generics, permissions, pagination

from users.serializers import *
from users.models.user import *
from users.functions.user_profile import *
from users.functions.student_profile import *
from users.functions.instructor_profile import *
from users.functions.dashboard_stats import *
from users.functions.password_reset import (
    RequestPasswordResetOTP,
    VerifyPasswordResetOTP,
    ConfirmPasswordReset,
)

### Pagination class ###
class CompanyPagination(pagination.PageNumberPagination):
    page_size = 9


class index(APIView):
    def get(self, request,*args,**kwargs):
        return HttpResponse("Welcome to Users")
    
    
### Create user profile ###
class CreateUserProfile(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request):
        x = UserProfileCreate(self, request)
        return x
    
### Create students profile ###
class CreateStudentProfile(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request):
        x = StudentProfileCreate(self, request)
        return x
    
### Create students profile ###
class CreateInstructorProfile(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request):
        x = InstructorProfileCreate(self, request)
        return x


class UserViewSet(ModelViewSet):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = UserLoginSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        # Allow access to own user data only, or whatever logic was intended
        # But for 'create' (POST), queryset isn't strictly used in the same way relative to object lookup
        # unless checking active state.
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            return User.objects.filter(pk=int(user_id))
        return User.objects.none()
    

class UserProfileListView(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = UserProfileSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        data = UserProfile.objects.filter(user=self.request.user).order_by('-id')
        return data
    

class StudentProfileListView(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = StudentsProfileSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        data = StudentProfile.objects.filter(user=self.request.user).order_by('-id')
        return data
    
class InstructorProfileListView(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = InstructorProfileSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        data = InstructorProfile.objects.filter(user=self.request.user).order_by('-id')
        return data

class UserProfileUpdateView(generics.UpdateAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def perform_update(self, serializer):
        serializer.save()

### Dashboard Stats ###
class DashboardStatsAPIView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        return GetDashboardStats(request)


### Password reset (email OTP) — public endpoints ###
def _client_ip(request):
    fwd = request.META.get('HTTP_X_FORWARDED_FOR')
    if fwd:
        return fwd.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _notify_admin_security(event, detail, request):
    """Best-effort admin security alert; never breaks the response."""
    try:
        from courses.services import notifications as _notify
        _notify.notify_admin_security_event(event, detail, ip=_client_ip(request))
    except Exception:
        pass


class PasswordResetRequestView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    def post(self, request):
        resp = RequestPasswordResetOTP(request)
        if getattr(resp, 'status_code', 500) < 400:
            _notify_admin_security(
                'Password reset requested',
                f"A password-reset OTP was requested for: "
                f"{request.data.get('email', '(unknown)')}",
                request,
            )
        return resp


class PasswordResetVerifyView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    def post(self, request):
        return VerifyPasswordResetOTP(request)


class PasswordResetConfirmView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    def post(self, request):
        resp = ConfirmPasswordReset(request)
        if getattr(resp, 'status_code', 500) < 400:
            _notify_admin_security(
                'Password changed',
                f"The password was reset/changed for: "
                f"{request.data.get('email', '(unknown)')}",
                request,
            )
        return resp
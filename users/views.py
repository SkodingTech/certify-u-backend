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
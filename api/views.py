from rest_framework.views import APIView
from django.http import HttpResponse
from rest_framework.permissions import ( IsAuthenticated,)
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics, mixins, status
from django.shortcuts import render,redirect
from django.urls import reverse
from rest_framework import generics, permissions, pagination
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from users.permissions import IsAdmin, IsSuperAdmin, IsTeamManager


from api.functions.blogs import PostBlogs, GetBlogs, DeleteBlogs
from api.functions.legal_docs import PostLegalDocs, GetLegalDocs, DeleteLegalDocs
from api.functions.messages import PostMessages
from api.functions.news_letter import PostNewsLetter
from api.functions.get_count import GetCount

from api.models import *
from api.serializers import *


class CompanyPagination(pagination.PageNumberPagination):
    page_size = 9

class index(APIView):
    def get(self, request,*args,**kwargs):
        return HttpResponse("Welcome to API")
    


#####################
##### POST View #####
#####################
class CreateMessages(APIView):
    def post(self, request, *args, **kwargs):
        data = PostMessages(self,request)
        return data
    
class CreateNewsLetter(APIView):
    def post(self, request, *args, **kwargs):
        data = PostNewsLetter(self,request)
        return data
    
class CreateBlogs(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAdmin,)
    parser_classes = (MultiPartParser, FormParser)
    def post(self, request, *args, **kwargs):
        data = PostBlogs(self,request)
        return data
    
class CreateLegalDocs(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsSuperAdmin,)
    def post(self, request, *args, **kwargs):
        data = PostLegalDocs(self,request)
        return data
    
    
######################
##### List Views #####
######################
class MessagesListView(generics.ListAPIView):
    serializer_class = MessagesSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        data=Messages.objects.filter(is_deleted=False).order_by('-id')
        return data
    
class NewsLetterListView(generics.ListAPIView):
    serializer_class = NewsLetterSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        data=NewsLetter.objects.filter(is_deleted=False).order_by('-id')
        return data
    
class BlogsListView(generics.ListAPIView):
    serializer_class = BlogsSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        data=Blogs.objects.filter(is_deleted=False).order_by('-id')
        return data
    
class LegalDocsListView(generics.ListAPIView):
    serializer_class = LegalDocsSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        data=LegalDocs.objects.filter(is_deleted=False).order_by('-id')
        return data
    
class HeroSectionListView(generics.ListAPIView):
    serializer_class = HeroSectionSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        data=HeroSection.objects.filter(is_deleted=False).order_by('-id')
        return data

class FunFactListView(generics.ListAPIView):
    serializer_class = FunFactSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        data=FunFact.objects.filter(is_deleted=False).order_by('-id')
        return data

class TestimonialListView(generics.ListAPIView):
    serializer_class = TestimonialSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        data=Testimonial.objects.filter(is_deleted=False).order_by('-id')
        return data

class BrandListView(generics.ListAPIView):
    serializer_class = BrandSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        data=Brand.objects.filter(is_deleted=False).order_by('-id')
        return data
#####################  
##### API Views #####
#####################   
class BlogsAPIView(APIView):
    def get(self,request,*args, **kwargs):
        data = GetBlogs(self, request)
        return data

class LegalDocsAPIView(APIView):
    def get(self,request,*args, **kwargs):
        data = GetLegalDocs(self, request)
        return data
    
class GetCountsAPIView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def get(self,request,*args, **kwargs):
        data = GetCount(self, request)
        return data

       
########################
##### Delete Views #####
########################   
class DeleteBlogsView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def get(self,request,*args, **kwargs):
        data = DeleteBlogs(self, request)
        return data
    
class DeleteLegalDocsView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def get(self,request,*args, **kwargs):
        data = DeleteLegalDocs(self, request)
        return data
    
    
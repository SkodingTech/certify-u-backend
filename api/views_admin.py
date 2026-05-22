"""Generic admin CRUD endpoints for site-content models.

Mirrors the Django admin coverage for HeroSection, Media, Careers, CareersApply,
FunFact, Testimonial, Brand, NewsLetter, Messages — all writable from the CMS.
"""
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import generics, pagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated

from api.models import (
    Brand, Careers, CareersApply, FunFact, HeroSection, Media, Messages,
    NewsLetter, Testimonial,
)
from api.serializers import (
    BrandSerializer, CareersApplySerializer, CareersSerializer,
    FunFactSerializer, HeroSectionSerializer, MediaSerializer,
    MessagesSerializer, NewsLetterSerializer, TestimonialSerializer,
)
from users.permissions import IsCMSAdmin


class AdminPagination(pagination.PageNumberPagination):
    page_size = 25


class _BaseListCreate(generics.ListCreateAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    pagination_class = AdminPagination
    parser_classes = (MultiPartParser, FormParser, JSONParser)


class _BaseDetail(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated, IsCMSAdmin)
    parser_classes = (MultiPartParser, FormParser, JSONParser)


# ── HeroSection ──────────────────────────────────────────────────────────────
class HeroSectionListCreate(_BaseListCreate):
    serializer_class = HeroSectionSerializer
    queryset = HeroSection.objects.filter(is_deleted=False).order_by('-id')


class HeroSectionDetail(_BaseDetail):
    serializer_class = HeroSectionSerializer
    queryset = HeroSection.objects.all()


# ── Media ─────────────────────────────────────────────────────────────────────
class MediaListCreate(_BaseListCreate):
    serializer_class = MediaSerializer
    queryset = Media.objects.filter(is_deleted=False).order_by('-id')


class MediaDetail(_BaseDetail):
    serializer_class = MediaSerializer
    queryset = Media.objects.all()


# ── Careers ──────────────────────────────────────────────────────────────────
class CareersListCreate(_BaseListCreate):
    serializer_class = CareersSerializer
    queryset = Careers.objects.filter(is_deleted=False).order_by('-id')


class CareersDetail(_BaseDetail):
    serializer_class = CareersSerializer
    queryset = Careers.objects.all()


# ── CareersApply ─────────────────────────────────────────────────────────────
class CareersApplyListCreate(_BaseListCreate):
    serializer_class = CareersApplySerializer
    queryset = CareersApply.objects.filter(is_deleted=False).order_by('-id')


class CareersApplyDetail(_BaseDetail):
    serializer_class = CareersApplySerializer
    queryset = CareersApply.objects.all()


# ── FunFact ──────────────────────────────────────────────────────────────────
class FunFactListCreate(_BaseListCreate):
    serializer_class = FunFactSerializer
    queryset = FunFact.objects.filter(is_deleted=False).order_by('-id')


class FunFactDetail(_BaseDetail):
    serializer_class = FunFactSerializer
    queryset = FunFact.objects.all()


# ── Testimonial ──────────────────────────────────────────────────────────────
class TestimonialListCreate(_BaseListCreate):
    serializer_class = TestimonialSerializer
    queryset = Testimonial.objects.filter(is_deleted=False).order_by('-id')


class TestimonialDetail(_BaseDetail):
    serializer_class = TestimonialSerializer
    queryset = Testimonial.objects.all()


# ── Brand ────────────────────────────────────────────────────────────────────
class BrandListCreate(_BaseListCreate):
    serializer_class = BrandSerializer
    queryset = Brand.objects.filter(is_deleted=False).order_by('-id')


class BrandDetail(_BaseDetail):
    serializer_class = BrandSerializer
    queryset = Brand.objects.all()


# ── NewsLetter (delete only via admin) ───────────────────────────────────────
class NewsLetterDetail(_BaseDetail):
    serializer_class = NewsLetterSerializer
    queryset = NewsLetter.objects.all()


# ── Messages (read + delete) ─────────────────────────────────────────────────
class MessagesDetail(_BaseDetail):
    serializer_class = MessagesSerializer
    queryset = Messages.objects.all()

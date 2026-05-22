from rest_framework import serializers
from users.models.user import *
from api.models import *

excludeData = ['updated_at', 'is_deleted']


class MessagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Messages
        exclude = excludeData


class BlogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blogs
        exclude = excludeData


class LegalDocsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalDocs
        exclude = excludeData


class NewsLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsLetter
        exclude = excludeData


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        exclude = excludeData


class HeroSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        exclude = excludeData


class FunFactSerializer(serializers.ModelSerializer):
    class Meta:
        model = FunFact
        exclude = excludeData


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        exclude = excludeData


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        exclude = excludeData


class CareersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Careers
        exclude = excludeData


class CareersApplySerializer(serializers.ModelSerializer):
    class Meta:
        model = CareersApply
        exclude = excludeData

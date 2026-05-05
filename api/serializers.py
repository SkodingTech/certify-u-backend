from rest_framework import serializers
from users.models.user import *
from api.models import *

excludeData = ['updated_at', 'is_deleted']

        
##### Messages Serializers #####
class MessagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Messages
        exclude = excludeData
          
        
##### Blogs Serializers #####     
class BlogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blogs
        exclude = excludeData

##### LegalDocs Serializers #####           
class LegalDocsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalDocs
        exclude = excludeData
        
##### NewsLetter Serializers #####           
class NewsLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsLetter
        exclude = excludeData
        
##### Media Serializers #####           
class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        exclude = excludeData

##### HeroSection Serializers #####
class HeroSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        exclude = excludeData

##### FunFact Serializers #####
class FunFactSerializer(serializers.ModelSerializer):
    class Meta:
        model = FunFact
        exclude = excludeData

##### Testimonial Serializers #####
class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        exclude = excludeData

##### Brand Serializers #####
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        exclude = excludeData
 
        
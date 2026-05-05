from django.db import models
import random
from ckeditor_uploader.fields import RichTextUploadingField


#### Blogs Path #### 
def blogsPath(self, filename):
    num = random.randint(100000000000,999999999999)
    url = "data/blog/%s/%s" % (num, filename)
    return url


#### Announcement Path #### 
def careersPath(self, filename):
    num = random.randint(100000000000,999999999999)
    url = "data/careers/%s/%s" % (num, filename)
    return url


#### FBM Path #### 
def mediaPath(self, filename):
    num = random.randint(100000000000,999999999999)
    url = "data/fbm/%s/%s" % (num, filename)
    return url

#### FunFact Path ####
def funFactPath(self, filename):
    num = random.randint(100000000000,999999999999)
    url = "data/funfact/%s/%s" % (num, filename)
    return url

#### Testimonial Path ####
def testimonialPath(self, filename):
    num = random.randint(100000000000,999999999999)
    url = "data/testimonial/%s/%s" % (num, filename)
    return url

#### Brand Path ####
def brandPath(self, filename):
    num = random.randint(100000000000,999999999999)
    url = "data/brand/%s/%s" % (num, filename)
    return url

class GeneralTimeStamp(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False,)
    class Meta:
        abstract = True
        
        
######################
#### Media Models ####
######################      
class Media(GeneralTimeStamp):
    file = models.FileField(blank=True, null=True, upload_to=mediaPath)
    media_type = models.CharField(max_length=20, blank=True, null=True)
    def __str__(self):
        return f"{self.id} media"    
        



#########################
#### Messages Models ####
#########################
class Messages(GeneralTimeStamp):
    meta_data = models.JSONField(blank=True, null=True)
    def __str__(self):
        return f"{self.id} messages"
      
######################
#### Blogs Models ####
######################
class Blogs(GeneralTimeStamp):
    name= models.CharField(max_length=255,blank=True,null=True)
    content = RichTextUploadingField(blank=True, null=True,)
    image = models.FileField(blank=True, null=True, upload_to=blogsPath, max_length=255)
    meta_data = models.JSONField(blank=True, null=True)
    def __str__(self):
        return f"{self.name} blogs"


    
########################
#### Careers Models ####
########################
class Careers(GeneralTimeStamp):
    name= models.CharField(max_length=255,blank=True,null=True)
    content = RichTextUploadingField(blank=True, null=True,)
    image = models.FileField(blank=True, null=True, upload_to=careersPath, max_length=255)
    meta_data = models.JSONField(blank=True, null=True)
    def __str__(self):
        return f"{self.name} careers"

class CareersApply(GeneralTimeStamp):
    name= models.CharField(max_length=255,blank=True,null=True)
    resume = models.FileField(blank=True, null=True, upload_to=careersPath, max_length=255)
    meta_data = models.JSONField(blank=True, null=True)
    def __str__(self):
        return f"{self.name} careers"
    
    
######################
#### Legal Models ####
######################
class LegalDocs(GeneralTimeStamp):
    terms =  RichTextUploadingField(blank=True, null=True,)
    privacy =  RichTextUploadingField(blank=True, null=True,)
    refund =  RichTextUploadingField(blank=True, null=True,)
    cookies =  RichTextUploadingField(blank=True, null=True,)
    def __str__(self):  
        return f"{self.id}"
    

####################
#### NewsLetter ####
####################
class NewsLetter(GeneralTimeStamp):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self):  
          return f"{self.email}"


########################
#### FunFact Models ####
########################
class FunFact(GeneralTimeStamp):
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    icon = models.FileField(blank=True, null=True, upload_to=funFactPath)
    count = models.CharField(max_length=50, blank=True, null=True) # E.g., "10k+"
    
    def __str__(self):
        return f"{self.title}"


############################
#### Testimonial Models ####
############################
class Testimonial(GeneralTimeStamp):
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255, blank=True, null=True)
    testimonial = models.TextField()
    avatar = models.ImageField(upload_to=testimonialPath, blank=True, null=True)
    rating = models.FloatField(default=5.0)
    
    def __str__(self):
        return f"{self.name} - {self.position}"


######################
#### Brand Models ####
######################
class Brand(GeneralTimeStamp):
    name = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to=brandPath)
    url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} Brand"

#### Hero Path #### 
def heroPath(self, filename):
    num = random.randint(100000000000,999999999999)
    url = "data/hero/%s/%s" % (num, filename)
    return url

######################
#### Hero Section ####
######################
class HeroSection(GeneralTimeStamp):
    title = models.CharField(max_length=255, blank=True, null=True)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    button_text = models.CharField(max_length=50, default="Explore Courses")
    image = models.FileField(blank=True, null=True, upload_to=heroPath)
    
    def __str__(self):
        return f"Hero Section - {self.title}"
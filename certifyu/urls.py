
from django.contrib import admin
from django.urls import path,include,re_path
from django.conf import settings
from rest_framework.routers import DefaultRouter
from django.views.static import serve

default_router = DefaultRouter(trailing_slash=False)


urlpatterns = [
    path('admin/', admin.site.urls),
    
    
    path('auth/', include(('rest_framework_social_oauth2.urls', 'social'), namespace='social')),
    path('oauth2/', include('oauth2_provider.urls', namespace='oauth2')),
    
    path('api/',include('api.urls')),
    path('users/',include('users.urls')),
    path('courses/',include('courses.urls')),
    
    re_path(r'^ckeditor/', include('ckeditor_uploader.urls')),
]

urlpatterns+= default_router.urls

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT
        }),
    ]


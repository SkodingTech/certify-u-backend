"""
SCORM URL Routing
Routes for SCORM API endpoints
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from scorm import views

# Create router for viewsets
router = DefaultRouter()
router.register(r'packages', views.ScormPackageViewSet, basename='scorm-package')

app_name = 'scorm'

urlpatterns = [
    # Viewset routes
    path('', include(router.urls)),

    # SCORM API endpoints
    path('init/', views.ScormInitializeView.as_view(), name='scorm-init'),
    path('set-value/', views.ScormSetValueView.as_view(), name='scorm-set-value'),
    path('get-value/', views.ScormGetValueView.as_view(), name='scorm-get-value'),
    path('commit/', views.ScormCommitView.as_view(), name='scorm-commit'),
    path('finish/', views.ScormFinishView.as_view(), name='scorm-finish'),

    # Tracking endpoints
    path('tracking/', views.ScormTrackingListView.as_view(), name='scorm-tracking-list'),
    path('tracking/<str:session_id>/', views.ScormTrackingDetailView.as_view(), name='scorm-tracking-detail'),

    # Attempts
    path('attempts/', views.ScormAttemptListView.as_view(), name='scorm-attempt-list'),
]

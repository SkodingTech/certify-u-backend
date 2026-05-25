from django.urls import path
from courses import views
from courses import views_extra as vx
from courses import views_admin as adm


urlpatterns = [
    path('', views.index.as_view(),name="courses_home"),
    
    ### Course View ###
    path('<int:id>/CourseAPIView', views.CourseAPIView.as_view()),
    path('<int:id>/CategoryAPIView', views.CategoryAPIView.as_view()),
    path('<int:id>/InstructorsAPIView', views.InstructorsAPIView.as_view()),
    
    ### List View ###
    path('CategoryListView', views.CategoryListView.as_view()),
    path('CourseListView', views.CourseListView.as_view()),
    path('<int:id>/ModuleListView', views.ModuleListView.as_view()),
    path('<int:id>/LessonListView', views.LessonListView.as_view()),
    path('<int:id>/CourseResourceListView', views.CourseResourceListView.as_view()),
    path('<int:id>/InstructorsAPIView', views.InstructorsAPIView.as_view()),
    
    path('EnrolledCourseListView', views.EnrolledCourseListView.as_view()),
    path('InstructorCourseListView', views.InstructorCourseListView.as_view()),
    path('InstructorListView', views.InstructorListView.as_view()),
    path('OrganizationListView', views.OrganizationListView.as_view()),
    path('EnrollmentListView', views.EnrollmentListView.as_view()),
    path('enrollments/<int:pk>/status/', views.EnrollmentStatusUpdateView.as_view()),
    path('InstructorEnrollmentListView', views.InstructorEnrollmentListView.as_view()),
    path('InstructorDiscussionListView', views.InstructorDiscussionListView.as_view()),
    path('EnrollCourse', views.EnrollCourseView.as_view()),
    path('<int:id>/CheckEnrollment', views.CheckEnrollmentView.as_view()),
    path('CreateCourse', views.CreateCourseView.as_view()),
    
    ### Review ###
    path('reviews/create/', views.ReviewCreateView.as_view()),
    path('<int:course_id>/reviews/', views.ReviewListView.as_view()),
    path('instructor/reviews/', views.InstructorReviewListView.as_view()),

    ### Live Sessions ###
    path('live-sessions/', views.LiveSessionListCreateView.as_view()),
    path('live-sessions/<int:pk>/', views.LiveSessionDetailView.as_view()),
    path('live-sessions/<int:pk>/join/', views.LiveSessionJoinView.as_view()),
    path('live-sessions/<int:pk>/attendance/', views.LiveSessionAttendanceView.as_view()),
    path('live-requests/', views.LiveSessionRequestListCreateView.as_view()),
    path('live-requests/<int:pk>/', views.LiveSessionRequestUpdateView.as_view()),
    path('instructor/status/', views.InstructorStatusUpdateView.as_view()),

    ### Presentation & Assessment ###
    path('<int:id>/PresentationListView', views.PresentationListView.as_view()),
    path('presentations/<int:pk>/progress/', views.PresentationProgressUpdateView.as_view()),
    path('lessons/<int:pk>/progress/', views.LessonProgressUpdateView.as_view()),
    
    path('<int:course_id>/assessment/', views.AssessmentDetailView.as_view()),
    path('<int:course_id>/assessment/start/', views.StartAssessmentView.as_view()),
    path('assessment/attempt/<int:attempt_id>/submit/', views.SubmitAssessmentView.as_view()),
    path('<int:id>/DeleteAssessmentQuestion', views.AssessmentQuestionAPIView.as_view()),

    ### Management APIs ###
    path('<int:course_id>/modules/<int:id>/ModuleAPIView', views.ModuleAPIView.as_view()),
    path('<int:module_id>/lessons/<int:id>/LessonAPIView', views.LessonAPIView.as_view()),
    path('<int:course_id>/resources/<int:id>/CourseResourceAPIView', views.CourseResourceAPIView.as_view()),

    ### Slot-based Booking ###
    path('availability/', vx.TrainerAvailabilityListCreateView.as_view()),
    path('availability/<int:pk>/', vx.TrainerAvailabilityDetailView.as_view()),
    path('slots/', vx.SlotListCreateView.as_view()),
    path('slots/<int:pk>/', vx.SlotDetailView.as_view()),
    path('slots/<int:slot_id>/check-in/', vx.SlotCheckInView.as_view()),
    path('slots/<int:slot_id>/check-out/', vx.SlotCheckOutView.as_view()),
    path('slots/<int:slot_id>/attendance/', vx.SlotAttendanceListView.as_view()),
    path('bookings/', vx.BookingListCreateView.as_view()),
    path('bookings/<int:pk>/cancel/', vx.BookingCancelView.as_view()),

    ### Trainer Onboarding & Verification ###
    path('trainer-documents/', vx.TrainerDocumentListCreateView.as_view()),
    path('trainer-documents/<int:pk>/review/', vx.TrainerDocumentReviewView.as_view()),
    path('instructors/<int:pk>/verification/', vx.InstructorVerificationStatusView.as_view()),
    path('instructors/<int:pk>/public/', vx.InstructorPublicProfileView.as_view()),

    ### Student Compliance Documents ###
    path('student-documents/', vx.StudentDocumentListCreateView.as_view()),
    path('student-documents/<int:pk>/review/', vx.StudentDocumentReviewView.as_view()),

    ### Job Roles ###
    path('job-roles/', vx.JobRoleListCreateView.as_view()),
    path('job-roles/<int:pk>/', vx.JobRoleDetailView.as_view()),

    ### Certificates ###
    path('certificates/', vx.MyCertificatesView.as_view()),
    path('certificates/admin/', vx.CertificateAdminListView.as_view()),
    path('certificates/issue/<int:enrollment_id>/', vx.CertificateIssueView.as_view()),
    path('certificates/<str:certificate_id>/download/', vx.CertificateDownloadView.as_view()),

    ### Certificate Templates (per-instructor) ###
    path('certificate-templates/', vx.CertificateTemplateListCreateView.as_view()),
    path('certificate-templates/<int:pk>/', vx.CertificateTemplateDetailView.as_view()),

    ### Schedule ###
    path('schedule/', vx.ScheduleView.as_view()),

    ### Customer Support ###
    path('support/channels/', vx.SupportChannelListView.as_view()),
    path('support/tickets/', vx.SupportTicketListCreateView.as_view()),
    path('support/tickets/<int:pk>/', vx.SupportTicketUpdateView.as_view()),
    path('support/whatsapp/webhook/', vx.WhatsAppWebhookView.as_view()),

    ### ── Admin / CMS endpoints (new) ───────────────────────────────────────
    path('admin/organizations/', adm.OrganizationListCreate.as_view()),
    path('admin/organizations/<int:pk>/', adm.OrganizationDetail.as_view()),

    path('admin/instructors/', adm.InstructorAdminList.as_view()),
    path('admin/instructors/<int:pk>/', adm.InstructorAdminDetail.as_view()),

    path('admin/trainer-availability/', adm.TrainerAvailabilityAdminList.as_view()),
    path('admin/trainer-availability/<int:pk>/', adm.TrainerAvailabilityAdminDetail.as_view()),

    path('admin/reviews/', adm.ReviewAdminList.as_view()),
    path('admin/reviews/<int:pk>/', adm.ReviewAdminDetail.as_view()),

    path('admin/assessment-attempts/', adm.AssessmentAttemptAdminList.as_view()),
    path('admin/assessment-attempts/<int:pk>/', adm.AssessmentAttemptAdminDetail.as_view()),

    path('admin/lesson-progress/', adm.LessonProgressAdminList.as_view()),
    path('admin/module-progress/', adm.ModuleProgressAdminList.as_view()),
    path('admin/presentation-progress/', adm.PresentationProgressAdminList.as_view()),

    path('admin/live-session-requests/', adm.LiveSessionRequestAdminList.as_view()),

    path('admin/discussions/', adm.DiscussionAdminList.as_view()),
    path('admin/discussion-replies/', adm.DiscussionReplyAdminList.as_view()),

    path('admin/regulatory-authorities/', adm.RegulatoryAuthorityListCreate.as_view()),
    path('admin/regulatory-authorities/<int:pk>/', adm.RegulatoryAuthorityDetail.as_view()),

    path('admin/regulatory-compliance/', adm.RegulatoryComplianceListCreate.as_view()),
    path('admin/regulatory-compliance/<int:pk>/', adm.RegulatoryComplianceDetail.as_view()),

    path('admin/regulatory-references/', adm.RegulatoryReferenceListCreate.as_view()),
    path('admin/regulatory-references/<int:pk>/', adm.RegulatoryReferenceDetail.as_view()),

    path('admin/compliance-documents/', adm.ComplianceDocumentListCreate.as_view()),
    path('admin/compliance-documents/<int:pk>/', adm.ComplianceDocumentDetail.as_view()),

    path('admin/student-documents/', adm.StudentDocumentAdminList.as_view()),
    path('admin/student-documents/<int:pk>/', adm.StudentDocumentAdminDetail.as_view()),

    path('admin/support-channels/', adm.SupportChannelListCreate.as_view()),
    path('admin/support-channels/<int:pk>/', adm.SupportChannelDetail.as_view()),
]
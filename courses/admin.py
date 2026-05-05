from django.contrib import admin
from courses.models import *

# --- Basic Registrations ---
admin.site.register(Category)
admin.site.register(Organization)
admin.site.register(Instructor)
admin.site.register(Lesson)
admin.site.register(Module)
admin.site.register(CourseResource)
admin.site.register(Discussion)
admin.site.register(DiscussionReply)
admin.site.register(Enrollment)
admin.site.register(LessonProgress)
admin.site.register(Review)
admin.site.register(LiveSession)
admin.site.register(LiveSessionRequest)
admin.site.register(SessionAttendance)
admin.site.register(RegulatoryReference)
admin.site.register(ComplianceDocument)
admin.site.register(AssessmentQuestion)

# --- Custom Admin Classes ---

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_approved', 'status', 'created_at')
    list_filter = ('is_approved', 'status')
    actions = ['approve_courses']

    def approve_courses(self, request, queryset):
        queryset.update(is_approved=True, status='published')
    approve_courses.short_description = "Approve selected courses"

@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'file_type', 'is_mandatory')
    list_filter = ('module__course', 'file_type', 'is_mandatory')

@admin.register(PresentationProgress)
class PresentationProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'presentation', 'completed', 'updated_at')
    search_fields = ('student__username', 'presentation__title')

@admin.register(ModuleProgress)
class ModuleProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'module', 'completed', 'updated_at')

class AssessmentQuestionInline(admin.StackedInline):
    model = AssessmentQuestion
    extra = 1

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'passing_score')
    inlines = [AssessmentQuestionInline]
    search_fields = ('title', 'course__title')

@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'assessment', 'score', 'passed', 'completed_at')
    list_filter = ('passed', 'assessment')
    search_fields = ('student__username', 'assessment__title')

@admin.register(RegulatoryAuthority)
class RegulatoryAuthorityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'website')

@admin.register(RegulatoryCompliance)
class RegulatoryComplianceAdmin(admin.ModelAdmin):
    list_display = ('title', 'regulation_type', 'is_mandatory', 'is_active')
    list_filter = ('regulation_type', 'is_mandatory', 'is_active')

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'enrollment', 'issued_at', 'is_revoked')
    list_filter = ('is_revoked',)
    search_fields = ('certificate_id', 'enrollment__student__username')
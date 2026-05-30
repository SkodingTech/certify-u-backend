from rest_framework import serializers
from courses.models import *
from courses.models.enrollment import Enrollment, ModuleProgress
from courses.models.presentation import Presentation, PresentationProgress
from courses.models.assessment import Assessment, AssessmentQuestion, AssessmentAttempt, Assessment
# Re-importing models to ensure they are available

excludeData = ['updated_at', 'is_deleted']


##### Category Serializers #####
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        exclude = excludeData
        read_only_fields = ['slug']

class InstructorSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Instructor
        exclude = excludeData

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        exclude = excludeData

##### Courses Serializers #####
class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    instructors = InstructorSerializer(many=True, read_only=True)
    
    class Meta:
        model = Course
        exclude = excludeData       
        
    def get_lessons_count(self, obj):
        # Sum lessons across all modules
        return Lesson.objects.filter(module__course=obj).count()  

class CourseCreateSerializer(serializers.ModelSerializer):
    # A brand-new trainer has no courses.Instructor record yet; the create
    # view (CreateCourseView.perform_create) auto-creates one and self-links
    # it. So instructors must NOT be a required input (and is read-only here to
    # stop a trainer attaching a course to someone else's instructor id).
    instructors = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    # Optional on create: slug auto-generates from title in Course.save();
    # categories can be attached later via the course edit flow.
    slug = serializers.SlugField(required=False, allow_blank=True)
    categories = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=Category.objects.all()
    )

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ('enrolled_students', 'rating', 'review_count', 'updated_at', 'is_deleted')
        
class LessonSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        exclude = excludeData
        read_only_fields = ['module']

    def get_is_completed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return LessonProgress.objects.filter(enrollment__student=user, lesson=obj, completed=True).exists()
        return False
        
class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        exclude = excludeData
        read_only_fields = ['course']

class CourseResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseResource
        exclude = excludeData
        read_only_fields = ['course']


class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    student_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Enrollment
        fields = ['id', 'course_title', 'student_name', 'status', 'created_at']

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}".strip() or obj.student.username

class DiscussionReplySerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_image = serializers.SerializerMethodField()

    class Meta:
        model = DiscussionReply
        fields = ['id', 'student_name', 'student_image', 'content', 'created_at']

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}".strip() or obj.student.username

    def get_student_image(self, obj):
        profile = getattr(obj.student, 'user_profile', None)
        return profile.image.url if profile and profile.image else None

class DiscussionSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_image = serializers.SerializerMethodField()
    course_title = serializers.CharField(source='course.title', read_only=True)
    replies_count = serializers.IntegerField(source='replies.count', read_only=True)

    class Meta:
        model = Discussion
        fields = ['id', 'student_name', 'student_image', 'course_title', 'title', 'content', 'replies_count', 'is_pinned', 'created_at']

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}".strip() or obj.student.username

    def get_student_image(self, obj):
        profile = getattr(obj.student, 'user_profile', None)
        return profile.image.url if profile and profile.image else None

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'course_title', 'rating', 'title', 'comment', 'created_at']
        read_only_fields = ['user', 'course_title']

    def get_user(self, obj):
        # Use user_profile instead of studentprofile to be consistent with UserLoginSerializer
        profile = getattr(obj.student, 'user_profile', None)
        return {
            "name": f"{obj.student.first_name} {obj.student.last_name}".strip() or obj.student.username,
            "profile_image": profile.image.url if profile and profile.image else None
        }
        
class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['course', 'rating', 'title', 'comment']

class LiveSessionSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    instructor_name = serializers.CharField(source='instructor.user.username', read_only=True)
    
    class Meta:
        model = LiveSession
        exclude = excludeData

class LiveSessionRequestSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.username', read_only=True)
    instructor_name = serializers.CharField(source='instructor.user.username', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True, allow_null=True)

    class Meta:
        model = LiveSessionRequest
        exclude = excludeData
        read_only_fields = ['student']

# --- New Serializers ---

class PresentationSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Presentation
        exclude = excludeData

    def get_is_completed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return PresentationProgress.objects.filter(student=user, presentation=obj, completed=True).exists()
        return False

class PresentationProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = PresentationProgress
        exclude = excludeData

class ModuleProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleProgress
        exclude = excludeData

class AssessmentQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentQuestion
        exclude = list(set(excludeData + ['correct_answer'])) # Hide correct answer

class AssessmentSerializer(serializers.ModelSerializer):
    # questions = AssessmentQuestionSerializer(many=True, read_only=True) 
    # Can opt to embed questions or fetch separately
    class Meta:
        model = Assessment
        exclude = excludeData

class AssessmentAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentAttempt
        exclude = excludeData


### Booking Serializers ###
class TrainerAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerAvailability
        exclude = excludeData
        read_only_fields = ['instructor']


class SlotSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    instructor_name = serializers.SerializerMethodField()
    seats_remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = Slot
        exclude = excludeData
        read_only_fields = ['seats_taken', 'instructor']

    def get_instructor_name(self, obj):
        u = obj.instructor.user
        return f"{u.first_name} {u.last_name}".strip() or u.username


class BookingSerializer(serializers.ModelSerializer):
    slot_detail = SlotSerializer(source='slot', read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        exclude = excludeData
        read_only_fields = ['student', 'booked_at', 'cancelled_at']

    def get_student_name(self, obj):
        u = obj.student
        return f"{u.first_name} {u.last_name}".strip() or u.username


### Job Role Serializer ###
class JobRoleSerializer(serializers.ModelSerializer):
    salary_range_display = serializers.CharField(read_only=True)

    class Meta:
        model = JobRole
        exclude = excludeData


### Trainer / Student Document Serializers ###
class TrainerDocumentSerializer(serializers.ModelSerializer):
    instructor_name = serializers.SerializerMethodField()

    class Meta:
        model = TrainerDocument
        exclude = excludeData
        read_only_fields = ['instructor', 'reviewed_by', 'reviewed_at', 'status', 'review_notes']

    def get_instructor_name(self, obj):
        u = obj.instructor.user
        return f"{u.first_name} {u.last_name}".strip() or u.username


class TrainerDocumentReviewSerializer(serializers.ModelSerializer):
    """Used by admins to review a document."""
    class Meta:
        model = TrainerDocument
        fields = ['status', 'review_notes']


class StudentDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentDocument
        exclude = excludeData
        read_only_fields = ['student', 'reviewed_by', 'reviewed_at', 'status', 'review_notes']


class StudentDocumentReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentDocument
        fields = ['status', 'review_notes']


### Certificate Serializer ###
class CertificateSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)
    student_name = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        exclude = excludeData

    def get_student_name(self, obj):
        u = obj.enrollment.student
        return f"{u.first_name} {u.last_name}".strip() or u.username

    def get_pdf_url(self, obj):
        if obj.pdf_file:
            try:
                return obj.pdf_file.url
            except Exception:
                return None
        return obj.download_url or None


### Support Serializers ###
class SupportChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportChannel
        exclude = excludeData


class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        exclude = excludeData
        read_only_fields = ['user', 'assigned_to', 'resolved_at']


### Instructor Public Profile / Verification ###
class InstructorVerificationSerializer(serializers.ModelSerializer):
    """Used by admins to set verification status on an instructor."""
    class Meta:
        model = Instructor
        fields = ['verification_status', 'verification_notes', 'verified']


class InstructorPublicProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)
    total_students = serializers.SerializerMethodField()
    total_courses = serializers.SerializerMethodField()
    total_successful_trainings = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Instructor
        fields = [
            'id', 'full_name', 'email', 'title', 'bio', 'profile_picture',
            'website', 'linkedin', 'x_link', 'verified', 'verification_status',
            'accreditation_summary',
            'total_students', 'total_courses', 'total_successful_trainings',
            'average_rating', 'review_count',
        ]

    def get_full_name(self, obj):
        u = obj.user
        return f"{u.first_name} {u.last_name}".strip() or u.username

    def get_total_courses(self, obj):
        return obj.courses.filter(is_deleted=False).count()

    def get_total_students(self, obj):
        return Enrollment.objects.filter(course__instructors=obj).values('student').distinct().count()

    def get_total_successful_trainings(self, obj):
        return Enrollment.objects.filter(course__instructors=obj, status='completed').count()

    def get_average_rating(self, obj):
        from django.db.models import Avg
        avg = Review.objects.filter(course__instructors=obj).aggregate(avg=Avg('rating'))['avg']
        return round(avg, 2) if avg is not None else 0

    def get_review_count(self, obj):
        return Review.objects.filter(course__instructors=obj).count()


### Extra admin-side serializers ###
from courses.models import (
    RegulatoryAuthority, RegulatoryCompliance, RegulatoryReference,
    ComplianceDocument,
)
from courses.models.enrollment import LessonProgress


class LessonProgressSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    course_title = serializers.CharField(source='lesson.module.course.title', read_only=True)

    class Meta:
        model = LessonProgress
        exclude = excludeData

    def get_student_name(self, obj):
        u = obj.enrollment.student
        return f"{u.first_name} {u.last_name}".strip() or u.username


class RegulatoryAuthoritySerializer(serializers.ModelSerializer):
    class Meta:
        model = RegulatoryAuthority
        exclude = excludeData


class RegulatoryComplianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegulatoryCompliance
        exclude = excludeData


class RegulatoryReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegulatoryReference
        exclude = excludeData


class ComplianceDocumentSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)

    class Meta:
        model = ComplianceDocument
        exclude = excludeData


class ReviewAdminSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'student_name', 'course_title', 'rating', 'title', 'comment',
                  'helpful_count', 'created_at']

    def get_student_name(self, obj):
        u = obj.student
        return f"{u.first_name} {u.last_name}".strip() or u.username


class AssessmentAttemptAdminSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)
    course_title = serializers.CharField(source='assessment.course.title', read_only=True)

    class Meta:
        model = AssessmentAttempt
        exclude = excludeData

    def get_student_name(self, obj):
        u = obj.student
        return f"{u.first_name} {u.last_name}".strip() or u.username


class LiveSessionRequestAdminSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = LiveSessionRequest
        exclude = excludeData

    def get_student_name(self, obj):
        u = obj.student
        return f"{u.first_name} {u.last_name}".strip() or u.username


from courses.models import CertificateTemplate

class CertificateTemplateSerializer(serializers.ModelSerializer):
    """Per-instructor certificate template (PDF upload + course attachments)."""
    instructor_name = serializers.SerializerMethodField()
    courses_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = CertificateTemplate
        fields = ["id", "title", "file", "preview", "status", "status_display",
                  "is_default", "notes", "courses", "instructor", "instructor_name",
                  "courses_count", "created_at", "updated_at"]
        read_only_fields = ["instructor", "created_at", "updated_at"]

    def get_instructor_name(self, obj):
        u = obj.instructor.user
        return f"{u.first_name} {u.last_name}".strip() or u.username

    def get_courses_count(self, obj):
        return obj.courses.count()


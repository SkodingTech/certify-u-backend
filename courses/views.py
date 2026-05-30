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
from courses.serializers import *
from courses.models import Course, Category, Instructor, Module, Lesson, CourseResource, Review, LiveSession, LiveSessionRequest, SessionAttendance, Organization
from courses.models.enrollment import Enrollment, ModuleProgress, LessonProgress
from courses.models.presentation import Presentation, PresentationProgress
from courses.models.assessment import Assessment, AssessmentAttempt, AssessmentQuestion
from courses.functions.course import GetCourses, PostCourse, DeleteCourse
from courses.functions.category import GetCategory, PostCategory, DeleteCategory
from courses.functions.instructors import GetInstructor
from courses.functions.module_lesson import PostModule, DeleteModule, PostLesson, DeleteLesson, PostResource, DeleteResource
from courses.functions.assessment import PostAssessment, DeleteAssessmentQuestion
from django.db.models import Count, Q
from django.utils import timezone


class CompanyPagination(pagination.PageNumberPagination):
    page_size = 50

class index(APIView):
    def get(self, request,*args,**kwargs):
        return HttpResponse("Welcome to Courses")
    
    
    
######################
##### List Views #####
######################
class CategoryListView(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CategorySerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        data = Category.objects.filter(is_deleted=False).order_by('-id')
        return data
    
class CourseListView(generics.ListAPIView):
    """Marketplace-grade course list with sort + filter params.

    Query parameters:
      type        : 'training' | 'accreditation'
      category    : Category slug (repeatable, ?category=a&category=b)
      provider    : Organization id (repeatable)
      instructor  : Instructor id (repeatable)
      level       : beginner|intermediate|advanced|mixed
      mode        : online|offline|hybrid
      price_min / price_max : numeric range
      q           : free-text search on title/subtitle/description
      sort        : popular | rating | price_low | price_high | latest | fastest
      featured    : 'true' to surface featured only
    """
    serializer_class = CourseSerializer
    pagination_class = CompanyPagination

    SORT_MAP = {
        'popular':    '-enrolled_students',
        'rating':     '-rating',
        'price_low':  'price',
        'price_high': '-price',
        'latest':     '-id',
        'fastest':    'duration_weeks',
    }

    def get_queryset(self, *args, **kwargs):
        qs = (Course.objects
              .filter(is_deleted=False, is_approved=True, status='published')
              .select_related('organization', 'regulatory_authority')
              .prefetch_related('instructors', 'instructors__user', 'categories'))
        params = self.request.query_params

        course_type = params.get('type')
        if course_type:
            qs = qs.filter(course_type=course_type)

        categories = params.getlist('category')
        if categories:
            qs = qs.filter(categories__slug__in=categories).distinct()

        providers = params.getlist('provider')
        if providers:
            qs = qs.filter(organization_id__in=providers)

        instructors = params.getlist('instructor')
        if instructors:
            qs = qs.filter(instructors__id__in=instructors).distinct()

        level = params.get('level')
        if level:
            qs = qs.filter(level=level)

        mode = params.get('mode')
        if mode:
            qs = qs.filter(delivery_mode=mode)

        price_min = params.get('price_min')
        if price_min:
            try: qs = qs.filter(price__gte=float(price_min))
            except ValueError: pass

        price_max = params.get('price_max')
        if price_max:
            try: qs = qs.filter(price__lte=float(price_max))
            except ValueError: pass

        q = params.get('q')
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(title__icontains=q) | Q(subtitle__icontains=q) | Q(description__icontains=q)
            )

        if params.get('featured', '').lower() == 'true':
            qs = qs.filter(featured=True)

        sort = params.get('sort', 'latest')
        order = self.SORT_MAP.get(sort, '-id')
        return qs.order_by(order, '-id')
    
class ModuleListView(generics.ListAPIView):
    serializer_class = ModuleSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        course = Course.objects.get(pk=self.kwargs['id'])
        data = Module.objects.filter(course=course, is_deleted=False).order_by('order', '-id')
        return data
    
class LessonListView(generics.ListAPIView):
    serializer_class = LessonSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        module = Module.objects.get(pk=self.kwargs['id'])
        data = Lesson.objects.filter(module=module, is_deleted=False).order_by('order', '-id')
        return data
    
class CourseResourceListView(generics.ListAPIView):
    serializer_class = CourseResourceSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        course = Course.objects.get(pk=self.kwargs['id'])
        data = CourseResource.objects.filter(course=course, is_deleted=False).order_by('-id')
        return data

class EnrolledCourseListView(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CourseSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        enrollments = Enrollment.objects.filter(student=self.request.user).values_list('course', flat=True)
        return (Course.objects
                .filter(id__in=enrollments, is_deleted=False)
                .select_related('organization')
                .prefetch_related('instructors', 'instructors__user', 'categories')
                .order_by('-id'))

def _caller_is_admin(user):
    """Treat Django staff/superuser or profile role ADMIN/SUPER_ADMIN as platform admin."""
    if not (user and user.is_authenticated):
        return False
    if user.is_staff or user.is_superuser:
        return True
    prof = getattr(user, 'user_profile', None) or getattr(user, 'userprofile', None)
    return bool(prof and getattr(prof, 'role', None) in ('ADMIN', 'SUPER_ADMIN'))


class InstructorCourseListView(generics.ListAPIView):
    """Instructor's own courses, or all courses when the caller is an admin (CMS view)."""
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CourseSerializer
    pagination_class = CompanyPagination

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        base = (Course.objects
                .filter(is_deleted=False)
                .select_related('organization', 'regulatory_authority')
                .prefetch_related('instructors', 'instructors__user', 'categories')
                .order_by('-id'))
        if _caller_is_admin(user):
            return base
        if hasattr(user, 'instructor'):
            return base.filter(instructors=user.instructor)
        if hasattr(user, 'instructorprofile'):
            return base.filter(instructors__user=user)
        return Course.objects.none()

class InstructorListView(generics.ListAPIView):
    # Public or Authenticated? Students need it.
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,) 
    serializer_class = InstructorSerializer
    pagination_class = CompanyPagination
    
    def get_queryset(self):
        return Instructor.objects.filter(is_deleted=False).order_by('?') # Randomize or order criteria

class OrganizationListView(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationSerializer
    pagination_class = CompanyPagination
    def get_queryset(self):
        return Organization.objects.filter(is_deleted=False).order_by('-id')

class EnrollmentListView(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = EnrollmentSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        data = Enrollment.objects.filter(student=self.request.user).order_by('-id')
        return data
    
    
#####################  
##### API Views #####
#####################   
class CourseAPIView(APIView):
    authentication_classes = (OAuth2Authentication,)
    parser_classes = (MultiPartParser, FormParser)

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self,request,*args, **kwargs):
        data = GetCourses(self, request)
        return data
    def post(self, request, *args, **kwargs):
        data = PostCourse(self, request)
        return data
    def delete(self, request, *args, **kwargs):
        data = DeleteCourse(self, request)
        return data
    
class CategoryAPIView(APIView):
    authentication_classes = (OAuth2Authentication,)

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self,request,*args, **kwargs):
        data = GetCategory(self, request)
        return data
    def post(self, request, *args, **kwargs):
        data = PostCategory(self, request)
        return data
    def delete(self, request, *args, **kwargs):
        data = DeleteCategory(self, request)
        return data
    
class InstructorsAPIView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request, id, *args, **kwargs):
        try:
            course = Course.objects.get(pk=id)
            instructors = course.instructors.filter(is_deleted=False)
            serializer = InstructorSerializer(instructors, many=True)
            return Response(serializer.data)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, id, *args, **kwargs):
        try:
            course = Course.objects.get(pk=id)
            instructor_id = request.data.get('instructor_id')
            action = request.data.get('action', 'add') # 'add' or 'remove'
            
            instructor = Instructor.objects.get(pk=instructor_id)
            if action == 'add':
                course.instructors.add(instructor)
            else:
                course.instructors.remove(instructor)
            
            return Response({"status": "success", "action": action})
        except (Course.DoesNotExist, Instructor.DoesNotExist):
            return Response({"error": "Course or Instructor not found"}, status=status.HTTP_404_NOT_FOUND)

class EnrollCourseView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request, *args, **kwargs):
        course_id = request.data.get('course_id')
        if not course_id:
            return Response({'error': 'Course ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
            
        enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)

        if created:
            from courses.services import notifications as _notify
            _notify.notify_enrollment(enrollment)
            return Response({'message': 'Enrolled successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Already enrolled'}, status=status.HTTP_200_OK)

class CheckEnrollmentView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        course_id = self.kwargs.get('id')
        if not course_id:
            return Response({'error': 'Course ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        is_enrolled = Enrollment.objects.filter(student=request.user, course_id=course_id).exists()
        return Response({'is_enrolled': is_enrolled}, status=status.HTTP_200_OK)

class CreateCourseView(generics.CreateAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CourseCreateSerializer
    
    def perform_create(self, serializer):
        user = self.request.user
        try:
            # Try to access the related Instructor model
            instructor = user.instructor
        except Exception:
            # If not found, create it (possibly using data from InstructorProfile if available)
            if hasattr(user, 'instructorprofile'):
                profile = user.instructorprofile
                instructor = Instructor.objects.create(
                    user=user,
                    title=profile.title,
                    bio=profile.bio,
                    profile_picture=profile.profile_picture,
                    website=profile.website,
                    linkedin=profile.linkedin,
                    x_link=profile.x_link,
                    verified=profile.verified
                )
            else:
                # Basic fallback
                instructor = Instructor.objects.create(user=user, title=user.username)
        
        course = serializer.save(is_approved=False, status='draft')
        course.instructors.add(instructor)
        # Assuming organization is required/optional, handled by serializer validation or null
        # If user has an organization, we could add it here too.

class ReviewCreateView(generics.CreateAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ReviewCreateSerializer

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

class ReviewListView(generics.ListAPIView):
    # authentication_classes = (OAuth2Authentication,) # Optional: if reviews are public
    # permission_classes = (IsAuthenticated,) # Optional
    serializer_class = ReviewSerializer
    pagination_class = CompanyPagination 
    
    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        return Review.objects.filter(course_id=course_id).order_by('-created_at')

class InstructorReviewListView(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ReviewSerializer
    pagination_class = CompanyPagination

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'instructor'):
            return Review.objects.filter(course__instructors=user.instructor).order_by('-created_at')
        if hasattr(user, 'instructorprofile'):
            return Review.objects.filter(course__instructors__user=user).order_by('-created_at')
        return Review.objects.none()

class InstructorEnrollmentListView(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = EnrollmentSerializer
    pagination_class = CompanyPagination

    def get_queryset(self):
        user = self.request.user
        if _caller_is_admin(user):
            queryset = Enrollment.objects.all().order_by('-created_at')
        else:
            instructor = getattr(user, 'instructor', None) or Instructor.objects.filter(user=user).first()
            if not instructor:
                return Enrollment.objects.none()
            queryset = Enrollment.objects.filter(course__instructors=instructor).order_by('-created_at')
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset

class InstructorDiscussionListView(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = DiscussionSerializer
    pagination_class = CompanyPagination

    def get_queryset(self):
        user = self.request.user
        if _caller_is_admin(user):
            queryset = Discussion.objects.all().order_by('-created_at')
        else:
            instructor = getattr(user, 'instructor', getattr(user, 'instructorprofile', None))
            if not instructor:
                return Discussion.objects.none()
            queryset = Discussion.objects.filter(course__instructors=instructor).order_by('-created_at')
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset


########################
##### Live Sessions ####
########################

class LiveSessionListCreateView(generics.ListCreateAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = LiveSessionSerializer

    def get_queryset(self):
        course_id = self.request.query_params.get('course_id')
        queryset = LiveSession.objects.all().order_by('start_time')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset

    def perform_create(self, serializer):
        try:
             instructor = self.request.user.instructor
        except:
             raise serializers.ValidationError("Only instructors can schedule sessions.")
        serializer.save(instructor=instructor)

class LiveSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = LiveSessionSerializer
    queryset = LiveSession.objects.all()

class LiveSessionJoinView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk, *args, **kwargs):
        try:
            session = LiveSession.objects.get(pk=pk)
        except LiveSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
        
        session.attendees.add(request.user)
        return Response({'status': 'joined', 'message': 'Successfully booked the session'})

class LiveSessionAttendanceView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk, *args, **kwargs):
        try:
            session = LiveSession.objects.get(pk=pk)
        except LiveSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # Create attendance record
        SessionAttendance.objects.get_or_create(session=session, student=request.user)
        
        return Response({'status': 'marked', 'message': 'Attendance marked'})

class LiveSessionRequestListCreateView(generics.ListCreateAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = LiveSessionRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if _caller_is_admin(user):
            return LiveSessionRequest.objects.all().order_by('-created_at')
        if hasattr(user, 'instructor'):
            return LiveSessionRequest.objects.filter(instructor=user.instructor).order_by('-created_at')
        return LiveSessionRequest.objects.filter(student=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

class LiveSessionRequestUpdateView(generics.UpdateAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = LiveSessionRequestSerializer
    queryset = LiveSessionRequest.objects.all()

class InstructorStatusUpdateView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            instructor = request.user.instructor
        except:
            return Response({'error': 'Instructor not found'}, status=status.HTTP_404_NOT_FOUND)
            
        is_online = request.data.get('is_online')
        if is_online is not None:
            instructor.is_online = is_online
            instructor.save()
            return Response({'status': 'success', 'is_online': instructor.is_online})
        return Response({'error': 'is_online field required'}, status=status.HTTP_400_BAD_REQUEST)

###########################
##### Presentation & Assessment #####
###########################

class PresentationListView(generics.ListAPIView):
    serializer_class = PresentationSerializer
    pagination_class = CompanyPagination
    def get_queryset(self, *args, **kwargs):
        module_id = self.kwargs.get('id')
        module = Module.objects.get(pk=module_id)
        return Presentation.objects.filter(module=module, is_deleted=False).order_by('order')

class PresentationProgressUpdateView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, pk, *args, **kwargs):
        try:
            presentation = Presentation.objects.get(pk=pk)
        except Presentation.DoesNotExist:
            return Response({'error': 'Presentation not found'}, status=status.HTTP_404_NOT_FOUND)

        progress, created = PresentationProgress.objects.get_or_create(student=request.user, presentation=presentation)
        progress.completed = True # Assuming full completion for now or use request.data.get('completed')
        progress.current_page = request.data.get('current_page', progress.current_page)
        progress.total_pages = request.data.get('total_pages', progress.total_pages)
        progress.save()

        # Check Module Completion
        check_module_completion(request.user, presentation.module)

        return Response({'status': 'progress_updated'}, status=status.HTTP_200_OK)

class EnrollmentStatusUpdateView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request, pk, *args, **kwargs):
        try:
            enrollment = Enrollment.objects.get(pk=pk)
            # Only instructor of the course or admin
            if not enrollment.course.instructors.filter(user=request.user).exists() and not request.user.is_staff:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            
            new_status = request.data.get('status')
            if new_status in dict(Enrollment.ENROLLMENT_STATUS):
                enrollment.status = new_status
                enrollment.save()
                return Response({'status': enrollment.status})
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        except Enrollment.DoesNotExist:
            return Response({'error': 'Enrollment not found'}, status=status.HTTP_404_NOT_FOUND)

def check_module_completion(user, module):
    # Check all mandatory presentations
    mandatory_presentations = Presentation.objects.filter(module=module, is_mandatory=True)
    completed_presentations_ids = PresentationProgress.objects.filter(
        student=user, 
        presentation__in=mandatory_presentations, 
        completed=True
    ).values_list('presentation_id', flat=True)
    
    presentations_done = mandatory_presentations.exclude(id__in=completed_presentations_ids).count() == 0

    # Check all lessons (assuming all are mandatory)
    all_lessons = Lesson.objects.filter(module=module)
    completed_lessons_ids = LessonProgress.objects.filter(
        enrollment__student=user,
        lesson__in=all_lessons,
        completed=True
    ).values_list('lesson_id', flat=True)

    lessons_done = all_lessons.exclude(id__in=completed_lessons_ids).count() == 0

    if presentations_done and lessons_done:
        enrollment = Enrollment.objects.filter(student=user, course=module.course).first()
        if enrollment:
            mod_progress, _ = ModuleProgress.objects.get_or_create(enrollment=enrollment, module=module)
            if not mod_progress.completed:
                mod_progress.completed = True
                mod_progress.completed_at = timezone.now()
                mod_progress.save()
            # Roll the module completion up to the overall enrollment progress/status
            recompute_enrollment_progress(enrollment)


def recompute_enrollment_progress(enrollment):
    """Recompute Enrollment.progress (0-100) and flip status to 'completed'.

    Progress model: completed modules drive the bulk of progress; when the
    course has an Assessment, passing it is the final gate (worth the last 10%
    and required to reach 'completed'). This is what was previously missing —
    nothing ever wrote Enrollment.progress / status, so completion never
    propagated and certificate issuance (gated on completion) always failed.
    """
    course = enrollment.course
    total_modules = Module.objects.filter(course=course, is_deleted=False).count()
    completed_modules = ModuleProgress.objects.filter(
        enrollment=enrollment, module__course=course, module__is_deleted=False, completed=True
    ).count()
    has_assessment = Assessment.objects.filter(course=course).exists()
    assessment_passed = AssessmentAttempt.objects.filter(
        student=enrollment.student, assessment__course=course, passed=True
    ).exists()

    module_fraction = (completed_modules / total_modules) if total_modules > 0 else 1.0
    content_done = (completed_modules == total_modules) if total_modules > 0 else True

    if has_assessment:
        progress = module_fraction * 90.0 + (10.0 if assessment_passed else 0.0)
        fully_complete = content_done and assessment_passed
    else:
        progress = module_fraction * 100.0
        fully_complete = content_done

    enrollment.progress = round(min(progress, 100.0), 2)
    if fully_complete:
        enrollment.progress = 100.0
        if enrollment.status != 'completed':
            enrollment.status = 'completed'
            enrollment.completed_at = timezone.now()
    enrollment.save()
    return enrollment

class LessonProgressUpdateView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, pk, *args, **kwargs):
        try:
            lesson = Lesson.objects.get(pk=pk)
        except Lesson.DoesNotExist:
            return Response({'error': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)

        enrollment = Enrollment.objects.filter(student=request.user, course=lesson.module.course).first()
        if not enrollment:
             return Response({'error': 'Not enrolled'}, status=status.HTTP_403_FORBIDDEN)

        progress, created = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
        progress.completed = True
        progress.save()
        # Check Module Completion
        check_module_completion(request.user, lesson.module)
        return Response({'status': 'progress_updated'}, status=status.HTTP_200_OK)

class AssessmentDetailView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, course_id, *args, **kwargs):
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if user is an instructor
        is_instructor = course.instructors.filter(user=request.user).exists()
        enrollment = None

        if not is_instructor:
            try:
                enrollment = Enrollment.objects.get(student=request.user, course=course)
            except Enrollment.DoesNotExist:
                return Response({'error': 'Enrollment not found'}, status=status.HTTP_404_NOT_FOUND)

            # Check if all modules are completed (only for students)
            
            # Determine total modules that actually have content
            modules_with_content = Module.objects.filter(course=course).annotate(
                lesson_count=Count('lessons', distinct=True),
                presentation_count=Count('presentations', distinct=True)
            ).filter(Q(lesson_count__gt=0) | Q(presentation_count__gt=0))
            
            total_modules = modules_with_content.count()
            
            # Check completion against these specific modules
            completed_modules = ModuleProgress.objects.filter(
                enrollment=enrollment, 
                completed=True,
                module__in=modules_with_content
            ).count()

            if completed_modules < total_modules:
                return Response({
                    'locked': True, 
                    'message': 'Complete all modules to unlock assessment',
                    'progress': f"{completed_modules}/{total_modules}"
                }, status=status.HTTP_403_FORBIDDEN)
        
        assessment = Assessment.objects.filter(course=course).first()
        if not assessment:
             return Response({'error': 'No assessment configured for this course'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AssessmentSerializer(assessment)
        data = serializer.data
        # Manually attach questions
        questions = AssessmentQuestion.objects.filter(assessment=assessment).order_by('order')
        data['questions'] = AssessmentQuestionSerializer(questions, many=True).data
        
        return Response(data)

    def post(self, request, course_id, *args, **kwargs):
        # Only instructors or admins should be able to create/update assessments
        data = PostAssessment(self, request)
        return data

class ModuleAPIView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request, course_id, id, *args, **kwargs):
        data = PostModule(self, request)
        return data
    def delete(self, request, course_id, id, *args, **kwargs):
        data = DeleteModule(self, request)
        return data

class LessonAPIView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request, module_id, id, *args, **kwargs):
        data = PostLesson(self, request)
        return data
    def delete(self, request, module_id, id, *args, **kwargs):
        data = DeleteLesson(self, request)
        return data

class CourseResourceAPIView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request, course_id, id, *args, **kwargs):
        data = PostResource(self, request)
        return data
    def delete(self, request, course_id, id, *args, **kwargs):
        data = DeleteResource(self, request)
        return data

class AssessmentQuestionAPIView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def delete(self, request, id, *args, **kwargs):
        data = DeleteAssessmentQuestion(self, request)
        return data

class StartAssessmentView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, course_id, *args, **kwargs):
        try:
            assessment = Assessment.objects.get(course_id=course_id)
        except Assessment.DoesNotExist:
            return Response({'error': 'Assessment not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # Check attempts logic if needed
        attempt = AssessmentAttempt.objects.create(student=request.user, assessment=assessment)
        return Response({'attempt_id': attempt.id, 'status': 'started'})

class SubmitAssessmentView(APIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request, attempt_id, *args, **kwargs):
        try:
            attempt = AssessmentAttempt.objects.get(pk=attempt_id, student=request.user)
        except AssessmentAttempt.DoesNotExist:
            return Response({'error': 'Attempt not found'}, status=status.HTTP_404_NOT_FOUND)
        answers = request.data.get('answers', {}) # Dict of {question_id: answer}
        score = 0
        total_points = 0
        questions = AssessmentQuestion.objects.filter(assessment=attempt.assessment)
        for q in questions:
            total_points += q.points
            user_ans = answers.get(str(q.id))
            if str(user_ans) == str(q.correct_answer): # Simple string comparison
                score += q.points

        percentage = (score / total_points) * 100 if total_points > 0 else 0
        attempt.score = percentage
        attempt.passed = percentage >= attempt.assessment.passing_score
        attempt.completed_at = timezone.now()
        attempt.save()

        # Roll up into enrollment progress/completion (passing the final
        # assessment is the completion gate when the course has one).
        enrollment = Enrollment.objects.filter(
            student=request.user, course=attempt.assessment.course
        ).first()
        if enrollment:
            recompute_enrollment_progress(enrollment)

        # Compute remaining attempts (0 means unlimited per model semantics)
        used_attempts = AssessmentAttempt.objects.filter(
            student=request.user, assessment=attempt.assessment
        ).count()
        max_attempts = attempt.assessment.max_attempts
        attempts_remaining = None if max_attempts == 0 else max(max_attempts - used_attempts, 0)

        # Encouragement + notification
        from courses.services import notifications as _notify
        _notify.notify_assessment_result(attempt)

        response_payload = {
            'score': percentage,
            'passed': attempt.passed,
            'status': 'completed',
            'attempts_used': used_attempts,
            'attempts_remaining': attempts_remaining,
        }
        if not attempt.passed:
            response_payload['encouragement_message'] = (
                attempt.assessment.encouragement_message
                or "Don't be discouraged — review the material and try again."
            )
        return Response(response_payload)
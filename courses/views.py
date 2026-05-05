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
    serializer_class = CourseSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        queryset = Course.objects.filter(is_deleted=False, is_approved=True, status='published').order_by('-id')
        course_type = self.request.query_params.get('type')
        if course_type:
            queryset = queryset.filter(course_type=course_type)
        return queryset
    
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
        # Return courses where the user is enrolled
        # Enrollment model has 'student' (User) and 'course' (Course)
        # We want the Course objects.
        enrollments = Enrollment.objects.filter(student=self.request.user).values_list('course', flat=True)
        data = Course.objects.filter(id__in=enrollments, is_deleted=False).order_by('-id')
        return data

class InstructorCourseListView(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CourseSerializer
    pagination_class = CompanyPagination
    def get_queryset(self,*args, **kwargs):
        # Return courses created by this instructor
        # Assuming user is linked via Instructor profile or directly
        if hasattr(self.request.user, 'instructor'):
             data = Course.objects.filter(instructors=self.request.user.instructor, is_deleted=False).order_by('-id')
             return data
        # Fallback for old model structure if needed
        if hasattr(self.request.user, 'instructorprofile'):
             data = Course.objects.filter(instructors__user=self.request.user, is_deleted=False).order_by('-id')
             return data
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
        instructor = getattr(user, 'instructor', None)
        if not instructor:
            instructor = Instructor.objects.filter(user=user).first()
            
        if instructor:
            queryset = Enrollment.objects.filter(course__instructors=instructor).order_by('-created_at')
            course_id = self.request.query_params.get('course')
            if course_id:
                queryset = queryset.filter(course_id=course_id)
            return queryset
        return Enrollment.objects.none()

class InstructorDiscussionListView(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = DiscussionSerializer
    pagination_class = CompanyPagination

    def get_queryset(self):
        user = self.request.user
        instructor = getattr(user, 'instructor', getattr(user, 'instructorprofile', None))
        if instructor:
            queryset = Discussion.objects.filter(course__instructors=instructor).order_by('-created_at')
            course_id = self.request.query_params.get('course')
            if course_id:
                queryset = queryset.filter(course_id=course_id)
            return queryset
        return Discussion.objects.none()


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
        if hasattr(user, 'instructor'):
             return LiveSessionRequest.objects.filter(instructor=user.instructor).order_by('-created_at')
        else:
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
            mod_progress.completed = True
            mod_progress.save()

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
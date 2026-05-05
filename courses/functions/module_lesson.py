from courses.models import Module, Lesson, Course, CourseResource
from courses.serializers import ModuleSerializer, LessonSerializer, CourseResourceSerializer
from rest_framework.response import Response
from rest_framework import status

### Module Functions ###
def PostModule(self, request):
    course_id = self.kwargs.get('course_id')
    module_id = self.kwargs.get('id')
    
    if module_id == 0:
        # Create
        try:
            course = Course.objects.get(pk=course_id)
            serializer = ModuleSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(course=course)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
    else:
        # Update
        try:
            module = Module.objects.get(pk=module_id, is_deleted=False)
            serializer = ModuleSerializer(module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Module.DoesNotExist:
            return Response({"error": "Module not found"}, status=status.HTTP_404_NOT_FOUND)

def DeleteModule(self, request):
    try:
        module = Module.objects.get(pk=self.kwargs['id'], is_deleted=False)
        module.is_deleted = True
        module.save()
        return Response({"message": "Module deleted successfully", "result": True})
    except Module.DoesNotExist:
        return Response({"error": "Module not found"}, status=status.HTTP_404_NOT_FOUND)

### Lesson Functions ###
def PostLesson(self, request):
    module_id = self.kwargs.get('module_id')
    lesson_id = self.kwargs.get('id')
    
    if lesson_id == 0:
        # Create
        try:
            module = Module.objects.get(pk=module_id)
            serializer = LessonSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(module=module)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Module.DoesNotExist:
            return Response({"error": "Module not found"}, status=status.HTTP_404_NOT_FOUND)
    else:
        # Update
        try:
            lesson = Lesson.objects.get(pk=lesson_id, is_deleted=False)
            serializer = LessonSerializer(lesson, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Lesson.DoesNotExist:
            return Response({"error": "Lesson not found"}, status=status.HTTP_404_NOT_FOUND)

def DeleteLesson(self, request):
    try:
        lesson = Lesson.objects.get(pk=self.kwargs['id'], is_deleted=False)
        lesson.is_deleted = True
        lesson.save()
        return Response({"message": "Lesson deleted successfully", "result": True})
    except Lesson.DoesNotExist:
        return Response({"error": "Lesson not found"}, status=status.HTTP_404_NOT_FOUND)

### Resource Functions ###
def PostResource(self, request):
    course_id = self.kwargs.get('course_id')
    resource_id = self.kwargs.get('id')
    
    if resource_id == 0:
        try:
            course = Course.objects.get(pk=course_id)
            serializer = CourseResourceSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(course=course)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
    else:
        try:
            resource = CourseResource.objects.get(pk=resource_id, is_deleted=False)
            serializer = CourseResourceSerializer(resource, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CourseResource.DoesNotExist:
            return Response({"error": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)

def DeleteResource(self, request):
    try:
        resource = CourseResource.objects.get(pk=self.kwargs['id'], is_deleted=False)
        resource.is_deleted = True
        resource.save()
        return Response({"message": "Resource deleted successfully", "result": True})
    except CourseResource.DoesNotExist:
        return Response({"error": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)

from courses.models import Course
from courses.serializers import CourseCreateSerializer, CourseSerializer
from rest_framework.response import Response
from rest_framework import status

### POST Functions ###
def PostCourse(self, request):
    if self.kwargs['id'] == 0:
        x = CourseCreateSerializer(data=request.data)
    else:
        try:
            obj = Course.objects.get(pk=self.kwargs['id'], is_deleted=False)
            x = CourseCreateSerializer(obj, data=request.data, partial=True)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
            
    if x.is_valid():
        x.save()
        return Response(x.data, status=status.HTTP_201_CREATED if self.kwargs['id'] == 0 else status.HTTP_200_OK)
    return Response(x.errors, status=status.HTTP_400_BAD_REQUEST)


### GET Functions ###
def GetCourses(self, request):
    try:
        data = Course.objects.get(pk=self.kwargs['id'], is_deleted=False)
        result = CourseSerializer(data)
        response = { 'data' : result.data }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404", "error": "Not Found"}, status=status.HTTP_404_NOT_FOUND)
    

### DELETE Functions ###
def DeleteCourse(self, request):
    try:
        data = Course.objects.get(pk=self.kwargs['id'], is_deleted=False)
        data.is_deleted = True
        data.save()
        response = { 'data' : "Deleted successfully", 'result': True }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404", "error": "Not Found"}, status=status.HTTP_404_NOT_FOUND)

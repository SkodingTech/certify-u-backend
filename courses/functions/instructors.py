from courses.models import Instructor
from courses.serializers import InstructorSerializer
from rest_framework.response import Response
from rest_framework import status

### POST Functions ###
def PostInstructor(self, request):
    if self.kwargs['id'] == 0:
        x = InstructorSerializer(data=request.data, is_deleted=False)
    else:
        obj = Instructor.objects.get(pk=self.kwargs['id'])
        x = InstructorSerializer(obj, data=request.data)
    if x.is_valid():
        x.save()
        return Response(x.data, status=status.HTTP_201_CREATED)
    return Response(x.errors, status=status.HTTP_400_BAD_REQUEST)


### GET Functions ###
def GetInstructor(self, request):
    try:
        data = Instructor.objects.get(pk=self.kwargs['id'], is_deleted=False)
        result = InstructorSerializer(data)
        response = { 'data' : result.data }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})
    

### GET Functions ###
def DeleteInstructor(self, request):
    try:
        data = Instructor.objects.get(pk=self.kwargs['id'], is_deleted=False)
        data.is_deleted = True
        data.save()
        response = { 'data' : "Deleted successfully", 'result': True }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})

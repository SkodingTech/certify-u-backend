from users.models.user import StudentProfile
from users.serializers import StudentsProfileSerializer
from rest_framework.response import Response
from rest_framework import status


def StudentProfileCreate(self, request):
    if self.kwargs['id'] == 0:
        x = StudentsProfileSerializer(data=request.data)
    else:
        obj = StudentProfile.objects.get(pk=self.kwargs['id'])
        x = StudentsProfileSerializer(obj, data=request.data)
    if x.is_valid():
        x.save()
        return Response(x.data, status=status.HTTP_201_CREATED)
    return Response(x.errors, status=status.HTTP_400_BAD_REQUEST)

def StudentProfileIdView(self, request):
    try:
        data = StudentProfile.objects.get(pk=self.kwargs['id'])
        result = StudentsProfileSerializer(data)
        response = { 'data' : result.data }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})

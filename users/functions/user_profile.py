from users.models.user import UserProfile
from users.serializers import UserProfileSerializer
from rest_framework.response import Response
from rest_framework import status


def UserProfileCreate(self, request):
    if self.kwargs['id'] == 0:
        x = UserProfileSerializer(data=request.data)
    else:
        obj = UserProfile.objects.get(pk=self.kwargs['id'])
        x = UserProfileSerializer(obj, data=request.data)
    if x.is_valid():
        x.save()
        return Response(x.data, status=status.HTTP_201_CREATED)
    return Response(x.errors, status=status.HTTP_400_BAD_REQUEST)

def UserProfileIdView(self, request):
    try:
        data = UserProfile.objects.get(pk=self.kwargs['id'])
        result = UserProfileSerializer(data)
        response = { 'data' : result.data }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})

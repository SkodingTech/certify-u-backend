from users.models.user import InstructorProfile
from users.serializers import InstructorProfileSerializer
from rest_framework.response import Response
from rest_framework import status


def InstructorProfileCreate(self, request):
    if self.kwargs.get('id', 0) == 0:
        # Create a mutable copy of the data if it isn't already
        data = request.data.copy()
        data['user'] = request.user.id
        x = InstructorProfileSerializer(data=data)
    else:
        obj = InstructorProfile.objects.get(pk=self.kwargs['id'])
        x = InstructorProfileSerializer(obj, data=request.data)
    if x.is_valid():
        instance = x.save()
        # Update UserProfile role to INSTRUCTOR
        try:
            user_profile = instance.user.user_profile
            user_profile.role = 'INSTRUCTOR'
            user_profile.save()
        except Exception as e:
            # Handle case where user_profile might not exist, though it should
            pass
        return Response(x.data, status=status.HTTP_201_CREATED)
    return Response(x.errors, status=status.HTTP_400_BAD_REQUEST)

def InstructorProfileIdView(self, request):
    try:
        data = InstructorProfile.objects.get(pk=self.kwargs['id'])
        result = InstructorProfileSerializer(data)
        response = { 'data' : result.data }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})

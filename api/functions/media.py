from api.models import Media
from api.serializers import MediaSerializer
from rest_framework.response import Response
from rest_framework import status

### POST Functions ###
def PostMedia(self, request):
    if self.kwargs['id'] == 0:
        x = MediaSerializer(data=request.data)
    else:
        obj = Media.objects.get(pk=self.kwargs['id'])
        x = MediaSerializer(obj, data=request.data)
    if x.is_valid():
        x.save()
        return Response(x.data, status=status.HTTP_201_CREATED)
    return Response(x.errors, status=status.HTTP_400_BAD_REQUEST)


### GET Functions ###
def GetMedia(self, request):
    try:
        data = Media.objects.get(pk=self.kwargs['id'], is_deleted=False)
        result = MediaSerializer(data)
        response = { 'data' : result.data }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})
    

### GET Functions ###
def DeleteMedia(self, request):
    try:
        data = Media.objects.get(pk=self.kwargs['id'])
        data.is_deleted = True
        data.save()
        response = { 'data' : "Deleted successfully", 'result': True }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})

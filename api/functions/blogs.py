from api.models import Blogs
from api.serializers import BlogsSerializer
from rest_framework.response import Response
from rest_framework import status

### POST Functions ###
def PostBlogs(self, request):
    if self.kwargs['id'] == 0:
        x = BlogsSerializer(data=request.data)
    else:
        obj = Blogs.objects.get(pk=self.kwargs['id'])
        x = BlogsSerializer(obj, data=request.data)
    if x.is_valid():
        x.save()
        return Response(x.data, status=status.HTTP_201_CREATED)
    return Response(x.errors, status=status.HTTP_400_BAD_REQUEST)


### GET Functions ###
def GetBlogs(self, request):
    try:
        data = Blogs.objects.get(pk=self.kwargs['id'], is_deleted=False)
        result = BlogsSerializer(data)
        response = { 'data' : result.data }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})
    

### GET Functions ###
def DeleteBlogs(self, request):
    try:
        data = Blogs.objects.get(pk=self.kwargs['id'])
        data.is_deleted = True
        data.save()
        response = { 'data' : "Deleted successfully", 'result': True }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})

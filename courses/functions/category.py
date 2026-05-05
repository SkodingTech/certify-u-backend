from courses.models import Category
from courses.serializers import CategorySerializer
from rest_framework.response import Response
from rest_framework import status

### POST Functions ###
def PostCategory(self, request):
    if self.kwargs['id'] == 0:
        x = CategorySerializer(data=request.data)
    else:
        try:
            obj = Category.objects.get(pk=self.kwargs['id'])
            x = CategorySerializer(obj, data=request.data)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
            
    if x.is_valid():
        x.save()
        return Response(x.data, status=status.HTTP_201_CREATED if self.kwargs['id'] == 0 else status.HTTP_200_OK)
    return Response(x.errors, status=status.HTTP_400_BAD_REQUEST)


### GET Functions ###
def GetCategory(self, request):
    try:
        data = Category.objects.get(pk=self.kwargs['id'], is_deleted=False)
        result = CategorySerializer(data)
        response = { 'data' : result.data }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})
    

### GET Functions ###
def DeleteCategory(self, request):
    try:
        data = Category.objects.get(pk=self.kwargs['id'], is_deleted=False)
        data.is_deleted = True
        data.save()
        response = { 'data' : "Deleted successfully", 'result': True }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})

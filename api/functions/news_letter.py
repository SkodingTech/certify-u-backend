from api.models import NewsLetter
from api.serializers import NewsLetterSerializer
from rest_framework.response import Response
from rest_framework import status

### POST Functions ###
def PostNewsLetter(self, request):
    x = NewsLetterSerializer(data=request.data)
    if x.is_valid():
        x.save()
        return Response(x.data, status=status.HTTP_201_CREATED)
    return Response(x.errors, status=status.HTTP_400_BAD_REQUEST)


### GET Functions ###
def GetNewsLetter(self, request):
    try:
        data = NewsLetter.objects.get(feed=self.kwargs['id'], user=request.user)
        result = NewsLetterSerializer(data)
        response = { 'data' : result.data }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})

from api.models import Messages
from api.serializers import MessagesSerializer
from rest_framework.response import Response
from rest_framework import status

### POST Functions ###
def PostMessages(self, request):
    x = MessagesSerializer(data=request.data)
    if x.is_valid():
        x.save()
        return Response(x.data, status=status.HTTP_201_CREATED)
    return Response(x.errors, status=status.HTTP_400_BAD_REQUEST)


### GET Functions ###
def GetMessages(self, request):
    try:
        data = Messages.objects.get(feed=self.kwargs['id'], user=request.user)
        result = MessagesSerializer(data)
        response = { 'data' : result.data }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})

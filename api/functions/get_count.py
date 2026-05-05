from api.models import NewsLetter, Messages
from api.serializers import NewsLetterSerializer
from rest_framework.response import Response
from rest_framework import status


### GET Functions ###
def GetCount(self, request):
    try:
        messages = Messages.objects.count()
        news = NewsLetter.objects.count()
        response = { "messages" : messages, "news":news,}
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})

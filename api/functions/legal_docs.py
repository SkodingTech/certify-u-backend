from api.models import LegalDocs
from api.serializers import LegalDocsSerializer
from rest_framework.response import Response
from rest_framework import status

### POST Functions ###
def PostLegalDocs(self, request):
    if self.kwargs['id'] == 0:
        x = LegalDocsSerializer(data=request.data)
    else:
        obj = LegalDocs.objects.get(pk=self.kwargs['id'])
        x = LegalDocsSerializer(obj, data=request.data)
    if x.is_valid():
        x.save()
        return Response(x.data, status=status.HTTP_201_CREATED)
    return Response(x.errors, status=status.HTTP_400_BAD_REQUEST)


### GET Functions ###
def GetLegalDocs(self, request):
    try:
        data = LegalDocs.objects.get(pk=self.kwargs['id'], is_deleted=False)
        result = LegalDocsSerializer(data)
        response = { 'data' : result.data }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})
    

### GET Functions ###
def DeleteLegalDocs(self, request):
    try:
        data = LegalDocs.objects.get(pk=self.kwargs['id'])
        data.is_deleted = True
        data.save()
        response = { 'data' : "Deleted successfully", 'result': True }
        return Response(response)
    except Exception as e:
        return Response({"status" : "404"})

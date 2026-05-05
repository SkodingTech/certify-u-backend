from django.urls import path
from api import views


urlpatterns = [
    path('', views.index.as_view(),name="api_home"),
    
    ### Post View ###
    path('CreateMessages', views.CreateMessages.as_view()),
    path('CreateNewsLetter', views.CreateNewsLetter.as_view()),
    path('<int:id>/CreateBlogs', views.CreateBlogs.as_view()),
    path('<int:id>/CreateLegalDocs', views.CreateLegalDocs.as_view()),
    
    ### List View ###
    path('MessagesListView', views.MessagesListView.as_view()),
    path('NewsLetterListView', views.NewsLetterListView.as_view()),
    path('BlogsListView', views.BlogsListView.as_view()),
    path('LegalDocsListView', views.LegalDocsListView.as_view()),
    path('HeroSectionListView', views.HeroSectionListView.as_view()),
    path('FunFactListView', views.FunFactListView.as_view()),
    path('TestimonialListView', views.TestimonialListView.as_view()),
    path('BrandListView', views.BrandListView.as_view()),
    
    ### Get View By ID ###
    path('<int:id>/BlogsAPIView', views.BlogsAPIView.as_view()),
    path('<int:id>/LegalDocsAPIView', views.LegalDocsAPIView.as_view()),
    path('GetCountsAPIView', views.GetCountsAPIView.as_view()),
    
    
    ### Delete By ID ###
    path('<int:id>/DeleteBlogsView', views.DeleteBlogsView.as_view()),
    path('<int:id>/DeleteLegalDocsView', views.DeleteLegalDocsView.as_view()),        
]
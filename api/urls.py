from django.urls import path
from api import views
from api import views_admin as va


urlpatterns = [
    path('', views.index.as_view(), name="api_home"),

    ### Existing POST View ###
    path('CreateMessages', views.CreateMessages.as_view()),
    path('CreateNewsLetter', views.CreateNewsLetter.as_view()),
    path('<int:id>/CreateBlogs', views.CreateBlogs.as_view()),
    path('<int:id>/CreateLegalDocs', views.CreateLegalDocs.as_view()),

    ### Existing List Views ###
    path('MessagesListView', views.MessagesListView.as_view()),
    path('NewsLetterListView', views.NewsLetterListView.as_view()),
    path('BlogsListView', views.BlogsListView.as_view()),
    path('LegalDocsListView', views.LegalDocsListView.as_view()),
    path('HeroSectionListView', views.HeroSectionListView.as_view()),
    path('FunFactListView', views.FunFactListView.as_view()),
    path('TestimonialListView', views.TestimonialListView.as_view()),
    path('BrandListView', views.BrandListView.as_view()),

    ### Existing Detail / Delete ###
    path('<int:id>/BlogsAPIView', views.BlogsAPIView.as_view()),
    path('<int:id>/LegalDocsAPIView', views.LegalDocsAPIView.as_view()),
    path('GetCountsAPIView', views.GetCountsAPIView.as_view()),
    path('<int:id>/DeleteBlogsView', views.DeleteBlogsView.as_view()),
    path('<int:id>/DeleteLegalDocsView', views.DeleteLegalDocsView.as_view()),

    ### ── Admin / CMS CRUD endpoints ───────────────────────────────────────
    path('admin/hero-sections/', va.HeroSectionListCreate.as_view()),
    path('admin/hero-sections/<int:pk>/', va.HeroSectionDetail.as_view()),

    path('admin/media/', va.MediaListCreate.as_view()),
    path('admin/media/<int:pk>/', va.MediaDetail.as_view()),

    path('admin/careers/', va.CareersListCreate.as_view()),
    path('admin/careers/<int:pk>/', va.CareersDetail.as_view()),

    path('admin/careers-applications/', va.CareersApplyListCreate.as_view()),
    path('admin/careers-applications/<int:pk>/', va.CareersApplyDetail.as_view()),

    path('admin/fun-facts/', va.FunFactListCreate.as_view()),
    path('admin/fun-facts/<int:pk>/', va.FunFactDetail.as_view()),

    path('admin/testimonials/', va.TestimonialListCreate.as_view()),
    path('admin/testimonials/<int:pk>/', va.TestimonialDetail.as_view()),

    path('admin/brands/', va.BrandListCreate.as_view()),
    path('admin/brands/<int:pk>/', va.BrandDetail.as_view()),

    path('admin/newsletter/<int:pk>/', va.NewsLetterDetail.as_view()),
    path('admin/messages/<int:pk>/', va.MessagesDetail.as_view()),
]

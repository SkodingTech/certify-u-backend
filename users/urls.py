from django.urls import path, include, re_path
from users import views
from users.views import UserViewSet

userList = UserViewSet.as_view({
    'post': 'create',
    'get': 'list'
})

urlpatterns = [
    path('', views.index.as_view(),name="users_home"),
     
     
    ### POST Urls ###
    path('user', userList, name='user-list'),
    path('CreateUserProfile', views.CreateUserProfile.as_view()),
    path('CreateStudentProfile', views.CreateStudentProfile.as_view()),
    path('CreateInstructorProfile', views.CreateInstructorProfile.as_view()),
    path('UserProfileUpdate', views.UserProfileUpdateView.as_view()),
     
    ### ListView Urls ###
    path('UserProfileListView', views.UserProfileListView.as_view()),
    path('StudentProfileListView', views.StudentProfileListView.as_view()),
    path('InstructorProfileListView', views.InstructorProfileListView.as_view()),
    path('dashboard-stats/', views.DashboardStatsAPIView.as_view()),
]
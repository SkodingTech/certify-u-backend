from django.contrib import admin
from users.models.user import UserProfile, InstructorProfile, StudentProfile


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('user__username', 'user__email', 'phone_number')

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(InstructorProfile)
admin.site.register(StudentProfile)
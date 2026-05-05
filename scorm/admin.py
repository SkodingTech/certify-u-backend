"""
Django Admin Configuration for SCORM Models
"""
from django.contrib import admin
from django.utils.html import format_html

from scorm.models import (
    ScormPackage, ScormModule, ScormSco,
    ScormTracking, ScormRuntimeData, ScormAttempt
)


@admin.register(ScormPackage)
class ScormPackageAdmin(admin.ModelAdmin):
    """Admin for SCORM Packages"""
    list_display = (
        'title', 'version', 'status_badge', 'total_modules',
        'total_scos', 'enrolled_users', 'published_at', 'created_at'
    )
    list_filter = ('status', 'version', 'created_at', 'is_active')
    search_fields = ('title', 'description')
    readonly_fields = (
        'id', 'file_size', 'total_scos', 'total_modules',
        'structure_tree', 'manifest_data', 'created_at',
        'updated_at', 'processing_task_id', 'error_message'
    )
    fieldsets = (
        ('Package Information', {
            'fields': ('title', 'description', 'version', 'language')
        }),
        ('Upload & Processing', {
            'fields': ('upload_file', 'file_size', 'status', 'processing_task_id'),
            'classes': ('collapse',),
        }),
        ('Content Structure', {
            'fields': ('entry_point', 'total_modules', 'total_scos', 'structure_tree'),
            'classes': ('collapse',),
        }),
        ('Manifest Data', {
            'fields': ('manifest_data',),
            'classes': ('collapse',),
        }),
        ('Publishing', {
            'fields': ('published_at', 'enrolled_users', 'is_active'),
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
        ('Errors', {
            'fields': ('error_message',),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        """Colored status badge"""
        colors = {
            'uploading': '#FFA500',
            'processing': '#00BFFF',
            'ready': '#00FF00',
            'error': '#FF0000',
            'archived': '#808080',
        }
        color = colors.get(obj.status, '#808080')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = 'Status'

    def has_delete_permission(self, request, obj=None):
        """Soft delete only"""
        return False


@admin.register(ScormModule)
class ScormModuleAdmin(admin.ModelAdmin):
    """Admin for SCORM Modules"""
    list_display = ('title', 'package', 'parent', 'order', 'visible', 'created_at')
    list_filter = ('package', 'visible', 'created_at')
    search_fields = ('title', 'identifier', 'package__title')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Module Information', {
            'fields': ('title', 'description', 'identifier')
        }),
        ('Organization', {
            'fields': ('package', 'parent', 'order')
        }),
        ('Content', {
            'fields': ('launch', 'resource_ref')
        }),
        ('Control', {
            'fields': ('visible', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ScormSco)
class ScormScoAdmin(admin.ModelAdmin):
    """Admin for SCORM SCOs"""
    list_display = (
        'title', 'module', 'is_asset_badge', 'score_max',
        'required', 'visible', 'created_at'
    )
    list_filter = ('module__package', 'is_asset', 'required', 'visible')
    search_fields = ('title', 'identifier', 'launch_url')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('SCO Information', {
            'fields': ('title', 'description', 'identifier')
        }),
        ('Organization', {
            'fields': ('package', 'module', 'order')
        }),
        ('Launch Configuration', {
            'fields': ('launch_url', 'resource_type', 'is_asset')
        }),
        ('Scoring', {
            'fields': ('score_min', 'score_max', 'max_time_allowed')
        }),
        ('Control', {
            'fields': ('visible', 'required', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def is_asset_badge(self, obj):
        """Asset badge"""
        if obj.is_asset:
            return format_html('<span style="color: green;">Asset</span>')
        return format_html('<span style="color: blue;">SCO</span>')

    is_asset_badge.short_description = 'Type'

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ScormTracking)
class ScormTrackingAdmin(admin.ModelAdmin):
    """Admin for SCORM Tracking"""
    list_display = (
        'user', 'package', 'lesson_status_badge', 'score_raw',
        'attempt_number', 'last_access', 'completion_date'
    )
    list_filter = (
        'lesson_status', 'package', 'is_passed',
        'last_access', 'first_access'
    )
    search_fields = ('user__username', 'package__title', 'session_id')
    readonly_fields = (
        'id', 'session_id', 'first_access', 'last_access',
        'created_at', 'updated_at'
    )
    fieldsets = (
        ('User & Package', {
            'fields': ('user', 'package', 'sco')
        }),
        ('Session', {
            'fields': ('session_id', 'ip_address', 'first_access', 'last_access')
        }),
        ('Completion', {
            'fields': (
                'lesson_status', 'entry_status', 'is_passed',
                'completion_date', 'attempt_number'
            )
        }),
        ('Scoring', {
            'fields': ('score_raw', 'score_scaled', 'score_min', 'score_max')
        }),
        ('Time Tracking', {
            'fields': ('time_spent',)
        }),
        ('Resume Data', {
            'fields': ('suspend_data', 'bookmark'),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def lesson_status_badge(self, obj):
        """Status badge"""
        colors = {
            'passed': '#00FF00',
            'completed': '#00FF00',
            'failed': '#FF0000',
            'incomplete': '#FFA500',
            'browsed': '#00BFFF',
            'not attempted': '#808080',
        }
        color = colors.get(obj.lesson_status, '#808080')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_lesson_status_display()
        )

    lesson_status_badge.short_description = 'Status'

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        """Tracking created via API, not admin"""
        return False


@admin.register(ScormRuntimeData)
class ScormRuntimeDataAdmin(admin.ModelAdmin):
    """Admin for SCORM Runtime Data"""
    list_display = ('tracking', 'element', 'value_preview', 'commit_count', 'last_committed')
    list_filter = ('element', 'commit_count', 'last_committed')
    search_fields = ('tracking__session_id', 'element', 'value')
    readonly_fields = ('id', 'commit_count', 'last_committed', 'created_at', 'updated_at')

    def value_preview(self, obj):
        """Show preview of value"""
        preview = str(obj.value)[:50]
        if len(str(obj.value)) > 50:
            preview += '...'
        return preview

    value_preview.short_description = 'Value Preview'

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        """Created via API"""
        return False


@admin.register(ScormAttempt)
class ScormAttemptAdmin(admin.ModelAdmin):
    """Admin for SCORM Attempts"""
    list_display = (
        'user', 'package', 'attempt_number', 'success_status_badge',
        'score_scaled', 'start_time', 'end_time'
    )
    list_filter = ('success_status', 'completion_status', 'start_time')
    search_fields = ('user__username', 'package__title', 'session_id')
    readonly_fields = ('id', 'start_time', 'created_at')

    def success_status_badge(self, obj):
        """Success status badge"""
        colors = {
            'passed': '#00FF00',
            'failed': '#FF0000',
            'unknown': '#808080',
        }
        color = colors.get(obj.success_status, '#808080')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_success_status_display()
        )

    success_status_badge.short_description = 'Success Status'

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        """Created via API"""
        return False

"""
Django REST Framework Serializers for SCORM Models
"""
from rest_framework import serializers
from django.contrib.auth.models import User

from scorm.models import (
    ScormPackage, ScormModule, ScormSco,
    ScormTracking, ScormRuntimeData, ScormAttempt
)


class UserSerializer(serializers.ModelSerializer):
    """Serialize User info"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class ScormScoSerializer(serializers.ModelSerializer):
    """Serialize SCORM SCO"""
    class Meta:
        model = ScormSco
        fields = [
            'id', 'identifier', 'title', 'description',
            'launch_url', 'resource_type', 'is_asset',
            'max_time_allowed', 'score_max', 'score_min',
            'order', 'visible', 'required', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ScormModuleSerializer(serializers.ModelSerializer):
    """Serialize SCORM Module"""
    scos = ScormScoSerializer(many=True, read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = ScormModule
        fields = [
            'id', 'identifier', 'title', 'description',
            'launch', 'order', 'visible', 'depth',
            'scos', 'children', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'depth']

    def get_children(self, obj):
        """Get child modules"""
        children = obj.children.all().order_by('order')
        return ScormModuleSerializer(children, many=True).data


class ScormPackageSerializer(serializers.ModelSerializer):
    """Serialize SCORM Package"""
    modules = ScormModuleSerializer(many=True, read_only=True)
    scos_count = serializers.IntegerField(source='total_scos', read_only=True)
    modules_count = serializers.IntegerField(source='total_modules', read_only=True)

    class Meta:
        model = ScormPackage
        fields = [
            'id', 'title', 'description', 'version',
            'file_size', 'status', 'entry_point',
            'total_scos', 'total_modules', 'scos_count', 'modules_count',
            'language', 'enrolled_users', 'published_at',
            'modules', 'structure_tree', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_size', 'status', 'entry_point',
            'total_scos', 'total_modules', 'modules',
            'structure_tree', 'created_at', 'updated_at',
            'error_message', 'processing_task_id'
        ]
        extra_kwargs = {
            'upload_file': {'write_only': True},
        }


class ScormPackageListSerializer(serializers.ModelSerializer):
    """Simplified serializer for package list"""
    class Meta:
        model = ScormPackage
        fields = [
            'id', 'title', 'version', 'status',
            'total_scos', 'total_modules',
            'enrolled_users', 'published_at', 'created_at'
        ]
        read_only_fields = fields


class ScormPackageUploadSerializer(serializers.ModelSerializer):
    """Serializer for SCORM package upload"""
    class Meta:
        model = ScormPackage
        fields = ['id', 'title', 'description', 'upload_file']
        extra_kwargs = {
            'upload_file': {'required': True},
        }

    def create(self, validated_data):
        """Create package and trigger async processing"""
        package = super().create(validated_data)

        # Get file size
        package.file_size = package.upload_file.size
        package.status = 'processing'
        package.save()

        # Import here to avoid circular imports
        from scorm.tasks import extract_and_parse_scorm_package

        # Trigger async task
        task = extract_and_parse_scorm_package.delay(package.id)
        package.processing_task_id = task.id
        package.save()

        return package


class ScormRuntimeDataSerializer(serializers.ModelSerializer):
    """Serialize SCORM Runtime Data"""
    class Meta:
        model = ScormRuntimeData
        fields = [
            'id', 'element', 'value', 'commit_count',
            'last_committed', 'updated_at'
        ]
        read_only_fields = ['id', 'last_committed', 'updated_at', 'commit_count']


class ScormTrackingSerializer(serializers.ModelSerializer):
    """Serialize SCORM Tracking"""
    user = UserSerializer(read_only=True)
    package = ScormPackageSerializer(read_only=True)
    sco = ScormScoSerializer(read_only=True)
    runtime_data = ScormRuntimeDataSerializer(many=True, read_only=True)

    class Meta:
        model = ScormTracking
        fields = [
            'id', 'session_id', 'user', 'package', 'sco',
            'lesson_status', 'entry_status', 'score_raw', 'score_scaled',
            'score_min', 'score_max', 'time_spent', 'attempt_number',
            'is_passed', 'first_access', 'last_access', 'completion_date',
            'suspend_data', 'bookmark', 'ip_address',
            'runtime_data', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'session_id', 'user', 'package', 'sco',
            'first_access', 'last_access', 'created_at', 'updated_at'
        ]


class ScormTrackingDetailSerializer(serializers.ModelSerializer):
    """Detailed tracking serializer with full runtime data"""
    user = UserSerializer(read_only=True)
    package = ScormPackageListSerializer(read_only=True)
    sco = ScormScoSerializer(read_only=True)
    cmi_data = serializers.SerializerMethodField()

    class Meta:
        model = ScormTracking
        fields = [
            'id', 'session_id', 'user', 'package', 'sco',
            'lesson_status', 'entry_status', 'score_raw', 'score_scaled',
            'time_spent', 'is_passed', 'attempt_number',
            'first_access', 'last_access', 'completion_date',
            'suspend_data', 'bookmark', 'cmi_data',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_cmi_data(self, obj):
        """Get all CMI data for tracking"""
        return ScormRuntimeData.get_all_values(obj)


class ScormAttemptSerializer(serializers.ModelSerializer):
    """Serialize SCORM Attempt"""
    user = UserSerializer(read_only=True)
    package = ScormPackageListSerializer(read_only=True)

    class Meta:
        model = ScormAttempt
        fields = [
            'id', 'user', 'package', 'attempt_number',
            'start_time', 'end_time', 'duration',
            'completion_status', 'success_status', 'score_scaled',
            'total_time', 'session_id', 'created_at'
        ]
        read_only_fields = fields


class ScormInitSerializer(serializers.Serializer):
    """Initialize SCORM session"""
    package_id = serializers.IntegerField(required=True)
    sco_id = serializers.IntegerField(required=False, allow_null=True)


class ScormSetValueSerializer(serializers.Serializer):
    """Set CMI value"""
    session_id = serializers.CharField(max_length=100)
    element = serializers.CharField(max_length=500)
    value = serializers.CharField(allow_blank=True)


class ScormGetValueSerializer(serializers.Serializer):
    """Get CMI value"""
    session_id = serializers.CharField(max_length=100)
    element = serializers.CharField(max_length=500)


class ScormCommitSerializer(serializers.Serializer):
    """Commit SCORM data"""
    session_id = serializers.CharField(max_length=100)


class ScormFinishSerializer(serializers.Serializer):
    """Finish SCORM session"""
    session_id = serializers.CharField(max_length=100)

from rest_framework import serializers

from files.models import FeatureRecord, GeospatialFile
from files.services.file_processor import validate_upload


class GeospatialFileUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = GeospatialFile
        fields = ["file"]

    def validate_file(self, uploaded_file):
        try:
            validate_upload(uploaded_file.name)
        except Exception as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return uploaded_file

    def create(self, validated_data):
        uploaded_file = validated_data["file"]
        return GeospatialFile.objects.create(
            filename=uploaded_file.name,
            file=uploaded_file,
        )


class GeospatialFileDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeospatialFile
        fields = [
            "id",
            "filename",
            "feature_count",
            "crs",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]


class FeatureMeasurementSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    index = serializers.IntegerField(source="feature_index")
    measurement = serializers.SerializerMethodField()

    class Meta:
        model = FeatureRecord
        fields = [
            "id",
            "index",
            "geometry_type",
            "geometry",
            "crs",
            "properties",
            "measurement",
        ]

    def get_measurement(self, obj):
        if obj.measurement_type == "none":
            return None

        payload = {
            "type": obj.measurement_type,
            "value": obj.measurement_value,
            "unit": obj.measurement_unit,
        }
        if obj.measurement_error:
            payload["error"] = obj.measurement_error
        return payload

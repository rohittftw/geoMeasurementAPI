from django.contrib import admin

from files.models import FeatureRecord, GeospatialFile


@admin.register(GeospatialFile)
class GeospatialFileAdmin(admin.ModelAdmin):
    list_display = ("filename", "status", "feature_count", "crs", "created_at")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(FeatureRecord)
class FeatureRecordAdmin(admin.ModelAdmin):
    list_display = (
        "geospatial_file",
        "feature_index",
        "geometry_type",
        "measurement_type",
        "measurement_value",
    )
    list_filter = ("geometry_type", "measurement_type")

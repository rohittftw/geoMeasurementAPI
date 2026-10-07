import uuid

from django.db import models


class ProcessingStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"


class GeospatialFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to="uploads/%Y/%m/%d/")
    crs = models.CharField(max_length=64, blank=True, default="")
    feature_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=16,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.filename} ({self.id})"


class FeatureRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    geospatial_file = models.ForeignKey(
        GeospatialFile,
        on_delete=models.CASCADE,
        related_name="features",
    )
    feature_index = models.PositiveIntegerField()
    geometry_type = models.CharField(max_length=64)
    geometry = models.JSONField()
    crs = models.CharField(max_length=64)
    properties = models.JSONField(default=dict)
    measurement_type = models.CharField(max_length=16, blank=True, default="")
    measurement_value = models.FloatField(null=True, blank=True)
    measurement_unit = models.CharField(max_length=16, blank=True, default="")
    measurement_error = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["feature_index"]
        unique_together = [("geospatial_file", "feature_index")]

    def __str__(self):
        return f"Feature {self.feature_index} ({self.geometry_type})"

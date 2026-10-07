from django.urls import path

from files.views import (
    GeospatialFileDetailView,
    GeospatialFileMeasurementsView,
    GeospatialFileUploadView,
)

urlpatterns = [
    path("files/", GeospatialFileUploadView.as_view(), name="file-upload"),
    path("files/<uuid:id>/", GeospatialFileDetailView.as_view(), name="file-detail"),
    path(
        "files/<uuid:id>/measurements/",
        GeospatialFileMeasurementsView.as_view(),
        name="file-measurements",
    ),
]

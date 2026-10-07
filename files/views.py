from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from files.models import FeatureRecord, GeospatialFile, ProcessingStatus
from files.serializers import (
    FeatureMeasurementSerializer,
    GeospatialFileDetailSerializer,
    GeospatialFileUploadSerializer,
)
from files.services.file_processor import FileProcessingError, process_geospatial_file


class GeospatialFileUploadView(APIView):
    def post(self, request):
        serializer = GeospatialFileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        geospatial_file = serializer.save()

        try:
            process_geospatial_file(geospatial_file)
        except FileProcessingError as exc:
            return Response(
                {
                    "id": str(geospatial_file.id),
                    "filename": geospatial_file.filename,
                    "status": geospatial_file.status,
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            return Response(
                {
                    "id": str(geospatial_file.id),
                    "filename": geospatial_file.filename,
                    "status": geospatial_file.status,
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            GeospatialFileDetailSerializer(geospatial_file).data,
            status=status.HTTP_201_CREATED,
        )


class GeospatialFileDetailView(generics.RetrieveAPIView):
    queryset = GeospatialFile.objects.all()
    serializer_class = GeospatialFileDetailSerializer
    lookup_field = "id"


class GeospatialFileMeasurementsView(generics.ListAPIView):
    serializer_class = FeatureMeasurementSerializer

    def get_queryset(self):
        file_id = self.kwargs["id"]
        return FeatureRecord.objects.filter(geospatial_file_id=file_id)

    def list(self, request, *args, **kwargs):
        file_id = self.kwargs["id"]
        geospatial_file = GeospatialFile.objects.filter(id=file_id).first()
        if geospatial_file is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if geospatial_file.status == ProcessingStatus.FAILED:
            return Response(
                {
                    "file_id": str(geospatial_file.id),
                    "status": geospatial_file.status,
                    "error": geospatial_file.error_message,
                    "features": [],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "file_id": str(geospatial_file.id),
                "filename": geospatial_file.filename,
                "crs": geospatial_file.crs,
                "feature_count": geospatial_file.feature_count,
                "features": serializer.data,
            }
        )

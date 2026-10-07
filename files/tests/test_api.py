import io
import zipfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from files.models import GeospatialFile, ProcessingStatus


SAMPLE_KML = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Test Point</name>
      <Point><coordinates>0,0,0</coordinates></Point>
    </Placemark>
    <Placemark>
      <name>Test Line</name>
      <LineString>
        <coordinates>0,0,0 0.01,0,0</coordinates>
      </LineString>
    </Placemark>
    <Placemark>
      <name>Test Polygon</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              0,0,0 0.001,0,0 0.001,0.001,0 0,0.001,0 0,0,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>
"""


class GeospatialAPIIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_upload_kml_and_fetch_measurements(self):
        upload = SimpleUploadedFile(
            "sample.kml",
            SAMPLE_KML.encode("utf-8"),
            content_type="application/vnd.google-earth.kml+xml",
        )
        response = self.client.post("/api/files/", {"file": upload}, format="multipart")
        self.assertEqual(response.status_code, 201)
        file_id = response.data["id"]
        self.assertEqual(response.data["status"], ProcessingStatus.COMPLETED)
        self.assertGreaterEqual(response.data["feature_count"], 3)

        detail = self.client.get(f"/api/files/{file_id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["id"], file_id)

        measurements = self.client.get(f"/api/files/{file_id}/measurements/")
        self.assertEqual(measurements.status_code, 200)
        self.assertEqual(measurements.data["feature_count"], detail.data["feature_count"])
        self.assertGreaterEqual(len(measurements.data["features"]), 3)

        geometry_types = {feature["geometry_type"] for feature in measurements.data["features"]}
        self.assertIn("Point", geometry_types)
        self.assertIn("LineString", geometry_types)
        self.assertIn("Polygon", geometry_types)

    def test_rejects_unsupported_extension(self):
        upload = SimpleUploadedFile(
            "notes.txt",
            b"not a geospatial file",
            content_type="text/plain",
        )
        response = self.client.post("/api/files/", {"file": upload}, format="multipart")
        self.assertEqual(response.status_code, 400)

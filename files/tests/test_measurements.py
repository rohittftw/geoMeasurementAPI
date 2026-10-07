from django.test import TestCase
from shapely.geometry import LineString, Point, Polygon

from files.services.crs import utm_epsg_for_point
from files.services.measurements import calculate_measurement


class MeasurementServiceTests(TestCase):
    def test_point_has_no_measurement(self):
        result = calculate_measurement(Point(0, 0), "EPSG:4326")
        self.assertEqual(result.measurement_type, "none")
        self.assertIsNone(result.value)

    def test_polygon_area_uses_projected_crs(self):
        # Small square near equator; area in m2 should be roughly 10,000 m2
        polygon = Polygon([(0, 0), (0.001, 0), (0.001, 0.001), (0, 0.001), (0, 0)])
        result = calculate_measurement(polygon, "EPSG:4326")
        self.assertEqual(result.measurement_type, "area")
        self.assertIsNotNone(result.value)
        self.assertGreater(result.value, 9000)
        self.assertLess(result.value, 13000)
        self.assertEqual(result.unit, "m2")

    def test_linestring_length_uses_projected_crs(self):
        line = LineString([(0, 0), (0.01, 0)])
        result = calculate_measurement(line, "EPSG:4326")
        self.assertEqual(result.measurement_type, "length")
        self.assertIsNotNone(result.value)
        self.assertGreater(result.value, 900)
        self.assertLess(result.value, 1300)
        self.assertEqual(result.unit, "m")

    def test_unsupported_geometry_is_handled(self):
        from shapely.geometry import GeometryCollection

        collection = GeometryCollection([Point(0, 0), LineString([(0, 0), (1, 1)])])
        result = calculate_measurement(collection, "EPSG:4326")
        self.assertEqual(result.measurement_type, "unsupported")
        self.assertIsNone(result.value)
        self.assertTrue(result.error)


class CRSServiceTests(TestCase):
    def test_utm_zone_northern_hemisphere(self):
        self.assertEqual(utm_epsg_for_point(0, 10), "EPSG:32631")

    def test_utm_zone_southern_hemisphere(self):
        self.assertEqual(utm_epsg_for_point(0, -10), "EPSG:32731")

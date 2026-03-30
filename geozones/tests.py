from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Check, Geozone


class GeozoneAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.polygon_wkt = (
            "POLYGON((50.12 53.18, 50.18 53.18, 50.18 53.22, 50.12 53.22, 50.12 53.18))"
        )
        self.geozone = Geozone.objects.create(
            name="Склад Самара",
            geometry=GEOSGeometry(self.polygon_wkt, srid=4326),
        )

    def test_create_geozone(self):
        response = self.client.post(
            "/api/geozones/",
            {"name": "Офис", "geometry": "POINT(50.15 53.20)"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Офис")
        self.assertEqual(Geozone.objects.count(), 2)

    def test_create_geozone_missing_name(self):
        response = self.client.post(
            "/api/geozones/",
            {"geometry": "POINT(50.15 53.20)"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_geozone_invalid_geometry(self):
        response = self.client.post(
            "/api/geozones/",
            {"name": "Bad", "geometry": "NOT_A_GEOMETRY"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_geozones(self):
        response = self.client.get("/api/geozones/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Склад Самара")


class CheckPointAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.geozone = Geozone.objects.create(
            name="Склад Самара",
            geometry=GEOSGeometry(
                "POLYGON((50.12 53.18, 50.18 53.18, 50.18 53.22, 50.12 53.22, 50.12 53.18))",
                srid=4326,
            ),
        )

    def test_point_inside_geozone(self):
        response = self.client.post(
            "/api/geozones/check-point/",
            {"device_id": "truck-42", "lat": 53.20, "lon": 50.15},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["inside"])
        self.assertEqual(response.data["matched_geozone"]["id"], self.geozone.id)
        self.assertEqual(response.data["matched_geozone"]["name"], "Склад Самара")

    def test_point_outside_geozone(self):
        response = self.client.post(
            "/api/geozones/check-point/",
            {"device_id": "truck-42", "lat": 53.10, "lon": 50.10},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["inside"])
        self.assertNotIn("matched_geozone", response.data)

    def test_check_saves_to_database(self):
        self.client.post(
            "/api/geozones/check-point/",
            {"device_id": "truck-42", "lat": 53.20, "lon": 50.15},
            format="json",
        )
        self.assertEqual(Check.objects.count(), 1)
        check = Check.objects.first()
        self.assertEqual(check.device_id, "truck-42")
        self.assertTrue(check.inside)
        self.assertEqual(check.matched_geozone, self.geozone)

    def test_invalid_lat(self):
        response = self.client.post(
            "/api/geozones/check-point/",
            {"device_id": "truck-42", "lat": 100, "lon": 50.15},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_lon(self):
        response = self.client.post(
            "/api/geozones/check-point/",
            {"device_id": "truck-42", "lat": 53.20, "lon": 200},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_device_id(self):
        response = self.client.post(
            "/api/geozones/check-point/",
            {"lat": 53.20, "lon": 50.15},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CheckHistoryAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.geozone = Geozone.objects.create(
            name="Склад Самара",
            geometry=GEOSGeometry(
                "POLYGON((50.12 53.18, 50.18 53.18, 50.18 53.22, 50.12 53.22, 50.12 53.18))",
                srid=4326,
            ),
        )
        Check.objects.create(
            device_id="truck-42",
            lat=53.20,
            lon=50.15,
            inside=True,
            matched_geozone=self.geozone,
        )
        Check.objects.create(
            device_id="truck-42",
            lat=53.10,
            lon=50.10,
            inside=False,
        )
        Check.objects.create(
            device_id="car-01",
            lat=53.20,
            lon=50.15,
            inside=True,
            matched_geozone=self.geozone,
        )

    def test_list_all_checks(self):
        response = self.client.get("/api/checks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_filter_by_device_id(self):
        response = self.client.get("/api/checks/?device_id=truck-42")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_inside(self):
        response = self.client.get("/api/checks/?inside=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertTrue(all(c["inside"] for c in response.data))

    def test_filter_combined(self):
        response = self.client.get("/api/checks/?device_id=truck-42&inside=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["device_id"], "truck-42")
        self.assertTrue(response.data[0]["inside"])

    def test_history_ordered_by_date_desc(self):
        response = self.client.get("/api/checks/")
        dates = [c["created_at"] for c in response.data]
        self.assertEqual(dates, sorted(dates, reverse=True))

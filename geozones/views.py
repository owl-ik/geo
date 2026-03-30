from django.db import connection
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Check, Geozone
from .serializers import CheckHistorySerializer, GeozoneSerializer, PointCheckSerializer


class GeozoneListCreateView(generics.ListCreateAPIView):
    queryset = Geozone.objects.all()
    serializer_class = GeozoneSerializer


class CheckPointView(APIView):
    def post(self, request):
        serializer = PointCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device_id = serializer.validated_data["device_id"]
        lat = serializer.validated_data["lat"]
        lon = serializer.validated_data["lon"]

        # Ищем геозону, содержащую точку.
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name
                FROM geozones_geozone
                WHERE ST_Contains(
                    geometry,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                )
                LIMIT 1
                """,
                [lon, lat],
            )
            row = cursor.fetchone()

        inside = bool(row)
        matched_geozone_id = row[0] if row else None
        matched_geozone_name = row[1] if row else None

        # Сохраняем результат проверки
        Check.objects.create(
            device_id=device_id,
            lat=lat,
            lon=lon,
            inside=inside,
            matched_geozone_id=matched_geozone_id,
        )

        response_data = {
            "device_id": device_id,
            "lat": lat,
            "lon": lon,
            "inside": inside,
        }
        if inside:
            response_data["matched_geozone"] = {
                "id": matched_geozone_id,
                "name": matched_geozone_name,
            }

        return Response(response_data, status=status.HTTP_200_OK)


class CheckHistoryView(generics.ListAPIView):
    serializer_class = CheckHistorySerializer

    def get_queryset(self):
        queryset = Check.objects.all()
        device_id = self.request.query_params.get("device_id")
        inside = self.request.query_params.get("inside")

        if device_id:
            queryset = queryset.filter(device_id=device_id)
        if inside is not None:
            inside_bool = inside.lower() == "true"
            queryset = queryset.filter(inside=inside_bool)

        return queryset

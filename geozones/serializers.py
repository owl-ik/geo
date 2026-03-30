from django.contrib.gis.geos import GEOSException, GEOSGeometry
from rest_framework import serializers

from .models import Check, Geozone


class GeozoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geozone
        fields = ["id", "name", "geometry"]

    def validate_geometry(self, value):
        if isinstance(value, str):
            try:
                GEOSGeometry(value)
            except (GEOSException, ValueError):
                raise serializers.ValidationError("Invalid geometry format.")
        return value


class PointCheckSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=255)
    lat = serializers.FloatField()
    lon = serializers.FloatField()

    def validate_lat(self, value):
        if not -90 <= value <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_lon(self, value):
        if not -180 <= value <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value


class CheckHistorySerializer(serializers.ModelSerializer):
    matched_geozone = GeozoneSerializer(read_only=True)

    class Meta:
        model = Check
        fields = [
            "id",
            "device_id",
            "lat",
            "lon",
            "inside",
            "matched_geozone",
            "created_at",
        ]

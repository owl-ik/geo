from django.contrib.gis.db import models


class Geozone(models.Model):
    name = models.CharField(max_length=255)
    geometry = models.GeometryField(srid=4326)

    def __str__(self):
        return self.name


class Check(models.Model):
    device_id = models.CharField(max_length=255, db_index=True)
    lat = models.FloatField()
    lon = models.FloatField()
    matched_geozone = models.ForeignKey(
        Geozone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checks",
    )
    inside = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

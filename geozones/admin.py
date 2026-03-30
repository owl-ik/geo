from django.contrib.gis import admin
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.forms.widgets import OSMWidget

from .models import Check, Geozone


@admin.register(Geozone)
class GeozoneAdmin(admin.GISModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    formfield_overrides = {
        gis_models.GeometryField: {"widget": OSMWidget},
    }


@admin.register(Check)
class CheckAdmin(admin.ModelAdmin):
    list_display = ("id", "device_id", "lat", "lon", "inside", "created_at")
    list_filter = ("inside", "device_id")

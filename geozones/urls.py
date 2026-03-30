from django.urls import path

from .views import CheckHistoryView, CheckPointView, GeozoneListCreateView

urlpatterns = [
    path("geozones/", GeozoneListCreateView.as_view(), name="geozone-list-create"),
    path("geozones/check-point/", CheckPointView.as_view(), name="check-point"),
    path("checks/", CheckHistoryView.as_view(), name="check-history"),
]

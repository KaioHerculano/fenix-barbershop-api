from django.urls import path

from barbers.views import BarberDetailView, BarberListView, BarberServicesView

urlpatterns = [
    path(
        "api/v1/companies/<slug:company_slug>/barbers/",
        BarberListView.as_view(),
        name="company-barber-list",
    ),
    path(
        "api/v1/companies/<slug:company_slug>/barbers/<uuid:barber_id>/",
        BarberDetailView.as_view(),
        name="company-barber-detail",
    ),
    path(
        "api/v1/companies/<slug:company_slug>/barbers/<uuid:barber_id>/services/",
        BarberServicesView.as_view(),
        name="company-barber-service-list",
    ),
]

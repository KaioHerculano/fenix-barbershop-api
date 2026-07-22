from django.urls import path

from services.views import ServiceDetailView, ServiceListView

urlpatterns = [
    path(
        "api/v1/companies/<slug:company_slug>/services/",
        ServiceListView.as_view(),
        name="company-service-list",
    ),
    path(
        "api/v1/companies/<slug:company_slug>/services/<uuid:service_id>/",
        ServiceDetailView.as_view(),
        name="company-service-detail",
    ),
]

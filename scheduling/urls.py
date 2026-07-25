from django.urls import path

from scheduling.views import (
    AppointmentCancelView,
    AppointmentCompleteView,
    AppointmentDetailView,
    AppointmentListCreateView,
    AppointmentRescheduleView,
    AvailabilityView,
    WorkingHourListView,
)

urlpatterns = [
    path(
        "api/v1/companies/<slug:company_slug>/working-hours/",
        WorkingHourListView.as_view(),
        name="company-working-hour-list",
    ),
    path(
        "api/v1/companies/<slug:company_slug>/scheduling/availability/",
        AvailabilityView.as_view(),
        name="company-appointment-availability",
    ),
    path(
        "api/v1/companies/<slug:company_slug>/appointments/",
        AppointmentListCreateView.as_view(),
        name="company-appointment-list-create",
    ),
    path(
        "api/v1/companies/<slug:company_slug>/appointments/<uuid:appointment_id>/",
        AppointmentDetailView.as_view(),
        name="company-appointment-detail",
    ),
    path(
        "api/v1/companies/<slug:company_slug>/appointments/<uuid:appointment_id>/cancel/",
        AppointmentCancelView.as_view(),
        name="company-appointment-cancel",
    ),
    path(
        "api/v1/companies/<slug:company_slug>/appointments/<uuid:appointment_id>/reschedule/",
        AppointmentRescheduleView.as_view(),
        name="company-appointment-reschedule",
    ),
    path(
        "api/v1/companies/<slug:company_slug>/appointments/<uuid:appointment_id>/complete/",
        AppointmentCompleteView.as_view(),
        name="company-appointment-complete",
    ),
]

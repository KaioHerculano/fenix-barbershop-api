from django.urls import path

from scheduling.views import WorkingHourListView

urlpatterns = [
    path(
        "api/v1/companies/<slug:company_slug>/working-hours/",
        WorkingHourListView.as_view(),
        name="company-working-hour-list",
    ),
]

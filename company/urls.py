from django.urls import path

from company.views import (
    StaffInvitationAcceptView,
    StaffInvitationCreateView,
    StaffInvitationDetailView,
)

urlpatterns = [
    path(
        "api/v1/companies/<slug:company_slug>/staff-invitations/",
        StaffInvitationCreateView.as_view(),
        name="company-staff-invitation-create",
    ),
    path(
        "api/v1/invitations/<str:token>/",
        StaffInvitationDetailView.as_view(),
        name="staff-invitation-detail",
    ),
    path(
        "api/v1/invitations/<str:token>/accept/",
        StaffInvitationAcceptView.as_view(),
        name="staff-invitation-accept",
    ),
]

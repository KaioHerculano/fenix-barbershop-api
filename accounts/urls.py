from django.urls import path

from accounts.views import OwnerRegistrationView

urlpatterns = [
    path(
        "api/v1/accounts/register/owner/",
        OwnerRegistrationView.as_view(),
        name="owner_registration",
    ),
]

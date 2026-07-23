from django.urls import path

from accounts.views import (
    CustomerRegistrationView,
    LoginView,
    OwnerRegistrationView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    TokenRefreshDocumentedView,
    UserMeView,
)

urlpatterns = [
    path(
        "api/v1/accounts/login/",
        LoginView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/v1/accounts/token/refresh/",
        TokenRefreshDocumentedView.as_view(),
        name="token_refresh",
    ),
    path(
        "api/v1/accounts/register/owner/",
        OwnerRegistrationView.as_view(),
        name="owner_registration",
    ),
    path(
        "api/v1/accounts/register/customer/",
        CustomerRegistrationView.as_view(),
        name="customer_registration",
    ),
    path(
        "api/v1/accounts/me/",
        UserMeView.as_view(),
        name="user_me",
    ),
    path(
        "api/v1/accounts/password-reset/",
        PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "api/v1/accounts/password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
]

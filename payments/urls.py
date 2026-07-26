from django.urls import path

from payments.views import PaymentCreateView, PaymentDetailView, PaymentWebhookView

urlpatterns = [
    path(
        "api/v1/payments/create/",
        PaymentCreateView.as_view(),
        name="payment-create",
    ),
    path(
        "api/v1/payments/<uuid:payment_id>/",
        PaymentDetailView.as_view(),
        name="payment-detail",
    ),
    path(
        "api/v1/payments/webhook/",
        PaymentWebhookView.as_view(),
        name="payment-webhook",
    ),
]

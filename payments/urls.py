from django.urls import path

from payments.views import PaymentCreateView, PaymentDetailView

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
]

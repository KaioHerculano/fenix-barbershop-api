from django.shortcuts import get_object_or_404

from payments.models import Payment


def get_user_payment(user, payment_id):
    return get_object_or_404(
        Payment.objects.select_related(
            "appointment",
            "appointment__company",
            "appointment__service",
        ),
        id=payment_id,
        user=user,
    )

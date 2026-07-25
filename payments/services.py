from uuid import uuid4

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from payments.models import Payment
from scheduling.models import Appointment


def build_payment_idempotency_key():
    return f"payment-create-{uuid4()}"


def validate_appointment_payable(appointment):
    if appointment.status == Appointment.Status.CANCELLED:
        raise ValidationError(
            {"appointment": "Agendamento cancelado nao pode ser pago."}
        )
    if appointment.status == Appointment.Status.COMPLETED:
        raise ValidationError(
            {"appointment": "Agendamento concluido nao pode ser pago."}
        )
    if appointment.status == Appointment.Status.EXPIRED:
        raise ValidationError(
            {"appointment": "Agendamento expirado nao pode ser pago."}
        )


def get_existing_payment_for_idempotency_key(user, idempotency_key):
    if not idempotency_key:
        return None

    payment = (
        Payment.objects.filter(idempotency_key=idempotency_key)
        .select_related("appointment", "appointment__service", "appointment__company")
        .first()
    )
    if not payment:
        return None
    if payment.user_id != user.id:
        raise ValidationError({"idempotency_key": "Chave de idempotencia invalida."})
    return payment


def create_payment_for_appointment(user, appointment_id, idempotency_key=None):
    with transaction.atomic():
        payment = get_existing_payment_for_idempotency_key(user, idempotency_key)
        if payment:
            return payment, False

        appointment = get_object_or_404(
            Appointment.objects.select_for_update().select_related(
                "company",
                "service",
                "customer",
            ),
            id=appointment_id,
            customer=user,
            company__is_active=True,
        )
        validate_appointment_payable(appointment)

        existing_pending_payment = (
            Payment.objects.select_for_update()
            .filter(
                appointment=appointment,
                status=Payment.Status.PENDING,
            )
            .select_related(
                "appointment", "appointment__service", "appointment__company"
            )
            .first()
        )
        if existing_pending_payment:
            return existing_pending_payment, False

        if Payment.objects.filter(
            appointment=appointment,
            status=Payment.Status.PAID,
        ).exists():
            raise ValidationError(
                {"appointment": "Agendamento ja possui pagamento pago."}
            )

        try:
            return (
                Payment.objects.create(
                    user=user,
                    appointment=appointment,
                    amount=appointment.service.price,
                    idempotency_key=idempotency_key or build_payment_idempotency_key(),
                ),
                True,
            )
        except IntegrityError:
            payment = (
                Payment.objects.filter(
                    appointment=appointment,
                    status=Payment.Status.PENDING,
                )
                .select_related(
                    "appointment", "appointment__service", "appointment__company"
                )
                .first()
            )
            if payment:
                return payment, False
            raise

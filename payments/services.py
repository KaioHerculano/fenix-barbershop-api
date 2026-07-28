from uuid import uuid4

from django.conf import settings
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from notifications.tasks import send_appointment_confirmation_email
from payments.gateways import get_payment_gateway
from payments.gateways.base import PixChargeRequest
from payments.models import Payment, PaymentWebhookEvent
from scheduling.models import Appointment


def build_payment_idempotency_key():
    return f"payment-create-{uuid4()}"


def build_payment_notification_url():
    if not settings.PAYMENT_WEBHOOK_BASE_URL:
        return ""
    return (
        f"{settings.PAYMENT_WEBHOOK_BASE_URL.rstrip('/')}{reverse('payment-webhook')}"
    )


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
            ensure_payment_charge(existing_pending_payment)
            return existing_pending_payment, False

        if Payment.objects.filter(
            appointment=appointment,
            status=Payment.Status.PAID,
        ).exists():
            raise ValidationError(
                {"appointment": "Agendamento ja possui pagamento pago."}
            )

        try:
            payment = Payment.objects.create(
                user=user,
                appointment=appointment,
                amount=appointment.service.price,
                idempotency_key=idempotency_key or build_payment_idempotency_key(),
            )
            ensure_payment_charge(payment)
            return payment, True
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
                ensure_payment_charge(payment)
                return payment, False
            raise


def ensure_payment_charge(payment):
    if payment.provider_payment_id:
        return payment

    charge_result = get_payment_gateway().create_pix_charge(
        PixChargeRequest(
            payment_id=str(payment.id),
            idempotency_key=payment.idempotency_key,
            amount=payment.amount,
            description=payment.appointment.service.name,
            payer_email=payment.user.email,
            notification_url=build_payment_notification_url(),
        )
    )
    apply_charge_result(payment, charge_result)
    return payment


def apply_charge_result(payment, charge_result):
    payment.provider = charge_result.provider
    payment.provider_payment_id = charge_result.provider_payment_id
    payment.payment_method = charge_result.payment_method
    payment.checkout_url = charge_result.checkout_url
    payment.payment_code = charge_result.payment_code
    payment.qr_code_base64 = charge_result.qr_code_base64
    payment.provider_payload = charge_result.provider_payload
    payment.expires_at = charge_result.expires_at
    payment.save(
        update_fields=[
            "provider",
            "provider_payment_id",
            "payment_method",
            "checkout_url",
            "payment_code",
            "qr_code_base64",
            "provider_payload",
            "expires_at",
            "updated_at",
        ]
    )


def process_payment_webhook(payload, headers=None, query_params=None, provider=None):
    headers = headers or {}
    query_params = query_params or {}
    webhook_result = get_payment_gateway(provider).parse_webhook(
        payload,
        headers,
        query_params,
    )
    with transaction.atomic():
        event, created = PaymentWebhookEvent.objects.get_or_create(
            provider=webhook_result.provider,
            provider_event_id=webhook_result.provider_event_id,
            defaults={
                "provider_payment_id": webhook_result.provider_payment_id,
                "event_type": webhook_result.event_type,
                "action": webhook_result.action,
                "raw_payload": webhook_result.raw_payload,
            },
        )
        if not created and event.processed_at:
            return event, False

        payment = get_object_or_404(
            Payment.objects.select_for_update(),
            provider=webhook_result.provider,
            provider_payment_id=webhook_result.provider_payment_id,
        )
        if webhook_result.paid and payment.status == Payment.Status.PENDING:
            payment.status = Payment.Status.PAID
            payment.paid_at = webhook_result.paid_at or timezone.now()
            payment.provider_payload = webhook_result.raw_payload
            payment.save(
                update_fields=[
                    "status",
                    "paid_at",
                    "provider_payload",
                    "updated_at",
                ]
            )
            confirm_paid_appointment(payment.appointment)
        elif webhook_result.paid and payment.status == Payment.Status.PAID:
            payment.provider_payload = webhook_result.raw_payload
            payment.save(update_fields=["provider_payload", "updated_at"])

        event.provider_payment_id = webhook_result.provider_payment_id
        event.event_type = webhook_result.event_type
        event.action = webhook_result.action
        event.raw_payload = webhook_result.raw_payload
        event.processed_at = timezone.now()
        event.save(
            update_fields=[
                "provider_payment_id",
                "event_type",
                "action",
                "raw_payload",
                "processed_at",
            ]
        )
        return event, True


def confirm_paid_appointment(appointment):
    if appointment.status == Appointment.Status.CONFIRMED:
        return appointment
    if appointment.status != Appointment.Status.PENDING:
        raise ValidationError({"appointment": "Agendamento nao pode ser confirmado."})

    appointment.status = Appointment.Status.CONFIRMED
    appointment.save(update_fields=["status", "updated_at"])
    transaction.on_commit(
        lambda: send_appointment_confirmation_email.delay(str(appointment.id))
    )
    return appointment


def cancel_pending_payments_for_appointment(appointment):
    return Payment.objects.filter(
        appointment=appointment,
        status=Payment.Status.PENDING,
    ).update(status=Payment.Status.CANCELLED, updated_at=timezone.now())

from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from loyalty.models import LoyaltyCard, LoyaltyTransaction
from scheduling.models import Appointment

POINTS_PER_COMPLETED_APPOINTMENT = 1


def get_or_create_locked_card(company, user):
    card, created = LoyaltyCard.objects.get_or_create(
        company=company,
        user=user,
        defaults={"points_balance": 0},
    )
    if created:
        return card
    return LoyaltyCard.objects.select_for_update().get(id=card.id)


def award_points_for_completed_appointment(appointment):
    if appointment.status != Appointment.Status.COMPLETED:
        raise ValidationError({"appointment": "Agendamento precisa estar concluido."})

    with transaction.atomic():
        card = get_or_create_locked_card(appointment.company, appointment.customer)
        if LoyaltyTransaction.objects.filter(
            appointment=appointment,
            type=LoyaltyTransaction.Type.EARN,
        ).exists():
            return None

        try:
            loyalty_transaction = LoyaltyTransaction.objects.create(
                card=card,
                company=appointment.company,
                user=appointment.customer,
                appointment=appointment,
                type=LoyaltyTransaction.Type.EARN,
                points=POINTS_PER_COMPLETED_APPOINTMENT,
                description=f"Pontos por agendamento concluido: {appointment.service.name}",
            )
        except IntegrityError:
            return None

        card.points_balance += POINTS_PER_COMPLETED_APPOINTMENT
        card.save(update_fields=["points_balance", "updated_at"])
        return loyalty_transaction


def redeem_points(user, company, points, description="Resgate de pontos"):
    if points <= 0:
        raise ValidationError(
            {"points": "Quantidade de pontos deve ser maior que zero."}
        )

    with transaction.atomic():
        card = get_or_create_locked_card(company, user)
        if card.points_balance < points:
            raise ValidationError({"points": "Saldo insuficiente para resgate."})

        loyalty_transaction = LoyaltyTransaction.objects.create(
            card=card,
            company=company,
            user=user,
            type=LoyaltyTransaction.Type.REDEEM,
            points=points,
            description=description or "Resgate de pontos",
        )
        card.points_balance -= points
        card.save(update_fields=["points_balance", "updated_at"])
        return loyalty_transaction


def adjust_points(user, company, points, description):
    if points == 0:
        raise ValidationError({"points": "Ajuste deve ter valor diferente de zero."})

    with transaction.atomic():
        card = get_or_create_locked_card(company, user)
        new_balance = card.points_balance + points
        if new_balance < 0:
            raise ValidationError({"points": "Ajuste deixaria saldo negativo."})

        loyalty_transaction = LoyaltyTransaction.objects.create(
            card=card,
            company=company,
            user=user,
            type=LoyaltyTransaction.Type.ADJUSTMENT,
            points=points,
            description=description,
        )
        card.points_balance = new_balance
        card.save(update_fields=["points_balance", "updated_at"])
        return loyalty_transaction

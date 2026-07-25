from datetime import date, time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APITestCase

from accounts.models import User
from barbers.models import BarberService
from company.models import Company, CompanyEmployee
from loyalty.models import LoyaltyCard, LoyaltyTransaction
from loyalty.selectors import get_user_loyalty_summary, get_user_loyalty_transactions
from loyalty.services import (
    adjust_points,
    award_points_for_completed_appointment,
    redeem_points,
)
from scheduling.models import Appointment
from scheduling.services import complete_appointment
from services.models import Service


class FakeData:
    def company(self, is_active=True):
        value = get_random_string(8).lower()
        return Company.objects.create(
            name=f"Barbearia {value}",
            slug=f"barbearia-{value}",
            is_active=is_active,
        )

    def user(self, full_name=None):
        value = get_random_string(10).lower()
        return User.objects.create_user(
            email=f"{value}@example.com",
            full_name=full_name or f"Pessoa {value}",
            password="StrongPass123!",
        )

    def employee(self, company, role, user=None, is_active=True):
        return CompanyEmployee.objects.create(
            user=user or self.user(),
            company=company,
            role=role,
            is_active=is_active,
        )

    def service(self, company, price=Decimal("50.00"), duration_minutes=30):
        value = get_random_string(8)
        return Service.objects.create(
            company=company,
            name=f"Servico {value}",
            price=price,
            duration_minutes=duration_minutes,
            is_active=True,
        )

    def appointment(
        self,
        company,
        customer,
        barber,
        service,
        status_value=Appointment.Status.CONFIRMED,
    ):
        start_time = time(9, 0)
        start_dt = timezone.datetime.combine(date.today(), start_time)
        return Appointment.objects.create(
            company=company,
            customer=customer,
            barber=barber,
            service=service,
            appointment_date=timezone.localdate() - timedelta(days=1),
            start_time=start_time,
            end_time=(start_dt + timedelta(minutes=service.duration_minutes)).time(),
            status=status_value,
            completed_at=(
                timezone.now() if status_value == Appointment.Status.COMPLETED else None
            ),
        )

    def assignment(self, barber, service):
        return BarberService.objects.create(
            barber=barber,
            service=service,
            is_active=True,
        )


class LoyaltyServiceTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.customer = self.fake.user()
        self.barber = self.fake.employee(self.company, User.Role.BARBER)
        self.owner = self.fake.employee(self.company, User.Role.OWNER)
        self.service = self.fake.service(self.company)
        self.fake.assignment(self.barber, self.service)

    def test_awards_points_for_completed_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            Appointment.Status.COMPLETED,
        )

        loyalty_transaction = award_points_for_completed_appointment(appointment)

        card = LoyaltyCard.objects.get(user=self.customer, company=self.company)
        self.assertEqual(card.points_balance, 1)
        self.assertEqual(loyalty_transaction.type, LoyaltyTransaction.Type.EARN)
        self.assertEqual(loyalty_transaction.points, 1)

    def test_rejects_award_for_non_completed_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            Appointment.Status.CONFIRMED,
        )

        with self.assertRaises(ValidationError):
            award_points_for_completed_appointment(appointment)

    def test_does_not_duplicate_points_for_same_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            Appointment.Status.COMPLETED,
        )

        first_transaction = award_points_for_completed_appointment(appointment)
        second_transaction = award_points_for_completed_appointment(appointment)

        card = LoyaltyCard.objects.get(user=self.customer, company=self.company)
        self.assertIsNotNone(first_transaction)
        self.assertIsNone(second_transaction)
        self.assertEqual(card.points_balance, 1)
        self.assertEqual(LoyaltyTransaction.objects.count(), 1)

    def test_redeems_points_with_sufficient_balance(self):
        card = LoyaltyCard.objects.create(
            company=self.company,
            user=self.customer,
            points_balance=3,
        )

        loyalty_transaction = redeem_points(
            self.customer,
            self.company,
            2,
            "Beneficio teste",
        )

        card.refresh_from_db()
        self.assertEqual(card.points_balance, 1)
        self.assertEqual(loyalty_transaction.type, LoyaltyTransaction.Type.REDEEM)
        self.assertEqual(loyalty_transaction.points, 2)

    def test_rejects_redeem_without_balance(self):
        with self.assertRaises(ValidationError):
            redeem_points(self.customer, self.company, 1)

    def test_rejects_redeem_with_invalid_points(self):
        with self.assertRaises(ValidationError):
            redeem_points(self.customer, self.company, 0)

    def test_rejects_adjustment_that_would_make_balance_negative(self):
        LoyaltyCard.objects.create(
            company=self.company,
            user=self.customer,
            points_balance=1,
        )

        with self.assertRaises(ValidationError):
            adjust_points(self.customer, self.company, -2, "Ajuste invalido")

    def test_summary_is_isolated_by_company(self):
        other_company = self.fake.company()
        LoyaltyCard.objects.create(
            company=self.company,
            user=self.customer,
            points_balance=2,
        )
        LoyaltyCard.objects.create(
            company=other_company,
            user=self.customer,
            points_balance=5,
        )

        summary = get_user_loyalty_summary(self.customer, self.company.slug)

        self.assertEqual(summary["total_points_balance"], 2)
        self.assertEqual(summary["cards"][0].company, self.company)

    def test_transactions_are_isolated_by_user(self):
        other_user = self.fake.user()
        card = LoyaltyCard.objects.create(
            company=self.company,
            user=self.customer,
            points_balance=1,
        )
        other_card = LoyaltyCard.objects.create(
            company=self.company,
            user=other_user,
            points_balance=1,
        )
        LoyaltyTransaction.objects.create(
            card=card,
            company=self.company,
            user=self.customer,
            type=LoyaltyTransaction.Type.EARN,
            points=1,
            description="Cliente correto",
        )
        LoyaltyTransaction.objects.create(
            card=other_card,
            company=self.company,
            user=other_user,
            type=LoyaltyTransaction.Type.EARN,
            points=1,
            description="Outro cliente",
        )

        transactions = list(get_user_loyalty_transactions(self.customer))

        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].user, self.customer)

    def test_owner_completes_appointment_and_awards_points(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
        )

        completed = complete_appointment(
            self.company.slug,
            appointment.id,
            self.owner.user,
        )

        card = LoyaltyCard.objects.get(user=self.customer, company=self.company)
        self.assertEqual(completed.status, Appointment.Status.COMPLETED)
        self.assertEqual(card.points_balance, 1)

    def test_assigned_barber_completes_appointment_and_awards_points(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
        )

        complete_appointment(self.company.slug, appointment.id, self.barber.user)

        self.assertTrue(
            LoyaltyTransaction.objects.filter(
                appointment=appointment,
                type=LoyaltyTransaction.Type.EARN,
            ).exists()
        )

    def test_customer_cannot_complete_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
        )

        with self.assertRaises(PermissionDenied):
            complete_appointment(self.company.slug, appointment.id, self.customer)

    def test_rejects_repeated_completion(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
        )
        complete_appointment(self.company.slug, appointment.id, self.owner.user)

        with self.assertRaises(ValidationError):
            complete_appointment(self.company.slug, appointment.id, self.owner.user)

        card = LoyaltyCard.objects.get(user=self.customer, company=self.company)
        self.assertEqual(card.points_balance, 1)

    def test_rejects_cancelled_completion(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            Appointment.Status.CANCELLED,
        )

        with self.assertRaises(ValidationError):
            complete_appointment(self.company.slug, appointment.id, self.owner.user)


class LoyaltyAPITests(APITestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.customer = self.fake.user()
        self.other_customer = self.fake.user()
        self.barber = self.fake.employee(self.company, User.Role.BARBER)
        self.owner = self.fake.employee(self.company, User.Role.OWNER)
        self.service = self.fake.service(self.company)
        self.fake.assignment(self.barber, self.service)

    def test_requires_authentication_to_view_summary(self):
        response = self.client.get(reverse("loyalty-me"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_empty_summary_for_authenticated_user(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(reverse("loyalty-me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_points_balance"], 0)
        self.assertEqual(response.data["cards"], [])

    def test_returns_summary_for_company_filter(self):
        LoyaltyCard.objects.create(
            company=self.company,
            user=self.customer,
            points_balance=4,
        )
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(
            reverse("loyalty-me"),
            {"company_slug": self.company.slug},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_points_balance"], 4)
        self.assertEqual(response.data["cards"][0]["company_slug"], self.company.slug)

    def test_lists_only_authenticated_user_transactions(self):
        card = LoyaltyCard.objects.create(
            company=self.company,
            user=self.customer,
            points_balance=1,
        )
        other_card = LoyaltyCard.objects.create(
            company=self.company,
            user=self.other_customer,
            points_balance=1,
        )
        LoyaltyTransaction.objects.create(
            card=card,
            company=self.company,
            user=self.customer,
            type=LoyaltyTransaction.Type.EARN,
            points=1,
            description="Cliente correto",
        )
        LoyaltyTransaction.objects.create(
            card=other_card,
            company=self.company,
            user=self.other_customer,
            type=LoyaltyTransaction.Type.EARN,
            points=1,
            description="Outro cliente",
        )
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(reverse("loyalty-transaction-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["description"], "Cliente correto")

    def test_redeems_points(self):
        LoyaltyCard.objects.create(
            company=self.company,
            user=self.customer,
            points_balance=3,
        )
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(
            reverse("loyalty-redeem"),
            {
                "company_slug": self.company.slug,
                "points": 2,
                "description": "Resgate API",
            },
            format="json",
        )

        card = LoyaltyCard.objects.get(company=self.company, user=self.customer)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["type"], LoyaltyTransaction.Type.REDEEM)
        self.assertEqual(card.points_balance, 1)

    def test_rejects_redeem_with_insufficient_balance(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(
            reverse("loyalty-redeem"),
            {"company_slug": self.company.slug, "points": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_complete_endpoint_awards_points_for_owner(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
        )
        self.client.force_authenticate(user=self.owner.user)

        response = self.client.patch(
            reverse(
                "company-appointment-complete",
                kwargs={
                    "company_slug": self.company.slug,
                    "appointment_id": appointment.id,
                },
            ),
            format="json",
        )

        card = LoyaltyCard.objects.get(company=self.company, user=self.customer)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Appointment.Status.COMPLETED)
        self.assertEqual(card.points_balance, 1)

    def test_complete_endpoint_rejects_unrelated_user(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
        )
        self.client.force_authenticate(user=self.other_customer)

        response = self.client.patch(
            reverse(
                "company-appointment-complete",
                kwargs={
                    "company_slug": self.company.slug,
                    "appointment_id": appointment.id,
                },
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

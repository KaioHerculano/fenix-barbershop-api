from datetime import time, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from accounts.models import User
from barbers.models import BarberService
from company.models import Company, CompanyEmployee
from payments.models import Payment
from payments.services import create_payment_for_appointment
from scheduling.models import Appointment
from services.models import Service


class FakeData:
    def company(self, is_active=True):
        value = get_random_string(8).lower()
        return Company.objects.create(
            name=f"Barbearia {value}",
            slug=f"barbearia-{value}",
            is_active=is_active,
        )

    def user(self, full_name=None, is_active=True):
        value = get_random_string(10).lower()
        return User.objects.create_user(
            email=f"{value}@example.com",
            full_name=full_name or f"Pessoa {value}",
            password="StrongPass123!",
            is_active=is_active,
        )

    def barber(self, company):
        return CompanyEmployee.objects.create(
            user=self.user(),
            company=company,
            role=User.Role.BARBER,
            is_active=True,
        )

    def service(self, company, price=Decimal("50.00")):
        value = get_random_string(8)
        return Service.objects.create(
            company=company,
            name=f"Servico {value}",
            price=price,
            duration_minutes=30,
            is_active=True,
        )

    def assignment(self, barber, service):
        return BarberService.objects.create(
            barber=barber,
            service=service,
            is_active=True,
        )

    def appointment(
        self,
        company,
        customer,
        barber,
        service,
        status=Appointment.Status.CONFIRMED,
    ):
        appointment_date = timezone.localdate() + timedelta(days=1)
        return Appointment.objects.create(
            company=company,
            customer=customer,
            barber=barber,
            service=service,
            appointment_date=appointment_date,
            start_time=time(9, 0),
            end_time=time(9, 30),
            status=status,
        )


class PaymentModelTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.customer = self.fake.user()
        self.barber = self.fake.barber(self.company)
        self.service = self.fake.service(self.company)
        self.fake.assignment(self.barber, self.service)
        self.appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
        )

    def test_creates_valid_payment(self):
        payment = Payment.objects.create(
            user=self.customer,
            appointment=self.appointment,
            amount=self.service.price,
            idempotency_key="payment-valid-key",
        )

        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.provider, Payment.Provider.INTERNAL)
        self.assertEqual(payment.amount, Decimal("50.00"))

    def test_rejects_invalid_amount(self):
        payment = Payment(
            user=self.customer,
            appointment=self.appointment,
            amount=Decimal("0.00"),
            idempotency_key="payment-invalid-amount",
        )

        with self.assertRaises(DjangoValidationError):
            payment.full_clean()

    def test_rejects_payment_for_other_customer_appointment(self):
        other_user = self.fake.user()
        payment = Payment(
            user=other_user,
            appointment=self.appointment,
            amount=self.service.price,
            idempotency_key="payment-other-customer",
        )

        with self.assertRaises(DjangoValidationError):
            payment.full_clean()


class PaymentServiceTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.customer = self.fake.user()
        self.other_customer = self.fake.user()
        self.barber = self.fake.barber(self.company)
        self.service = self.fake.service(self.company, price=Decimal("75.90"))
        self.fake.assignment(self.barber, self.service)
        self.appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
        )

    def test_creates_payment_using_service_price(self):
        payment, created = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "payment-create-key",
        )

        self.assertTrue(created)
        self.assertEqual(payment.amount, Decimal("75.90"))
        self.assertEqual(payment.appointment, self.appointment)

    def test_returns_same_payment_for_same_idempotency_key(self):
        first_payment, first_created = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "payment-same-key",
        )
        second_payment, second_created = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "payment-same-key",
        )

        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(second_payment.id, first_payment.id)
        self.assertEqual(Payment.objects.count(), 1)

    def test_returns_existing_pending_payment_for_same_appointment(self):
        first_payment, first_created = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "payment-first-key",
        )
        second_payment, second_created = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "payment-second-key",
        )

        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(second_payment.id, first_payment.id)
        self.assertEqual(Payment.objects.count(), 1)

    def test_rejects_idempotency_key_from_other_user(self):
        create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "payment-private-key",
        )

        with self.assertRaises(ValidationError):
            create_payment_for_appointment(
                self.other_customer,
                self.appointment.id,
                "payment-private-key",
            )

    def test_rejects_cancelled_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            status=Appointment.Status.CANCELLED,
        )

        with self.assertRaises(ValidationError):
            create_payment_for_appointment(
                self.customer,
                appointment.id,
                "payment-cancelled-appointment",
            )

    def test_rejects_completed_appointment(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            status=Appointment.Status.COMPLETED,
        )

        with self.assertRaises(ValidationError):
            create_payment_for_appointment(
                self.customer,
                appointment.id,
                "payment-completed-appointment",
            )

    def test_rejects_appointment_with_paid_payment(self):
        Payment.objects.create(
            user=self.customer,
            appointment=self.appointment,
            amount=self.service.price,
            status=Payment.Status.PAID,
            idempotency_key="payment-paid-key",
            paid_at=timezone.now(),
        )

        with self.assertRaises(ValidationError):
            create_payment_for_appointment(
                self.customer,
                self.appointment.id,
                "payment-after-paid-key",
            )


class PaymentAPITests(APITestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.customer = self.fake.user()
        self.other_customer = self.fake.user()
        self.barber = self.fake.barber(self.company)
        self.service = self.fake.service(self.company)
        self.fake.assignment(self.barber, self.service)
        self.appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
        )

    def create_url(self):
        return reverse("payment-create")

    def detail_url(self, payment):
        return reverse("payment-detail", kwargs={"payment_id": payment.id})

    def test_requires_authentication_to_create_payment(self):
        response = self.client.post(self.create_url(), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_creates_payment(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(
            self.create_url(),
            {"appointment_id": str(self.appointment.id)},
            HTTP_IDEMPOTENCY_KEY="api-payment-key",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["appointment_id"], str(self.appointment.id))
        self.assertEqual(response.data["amount"], "50.00")
        self.assertEqual(response.data["status"], Payment.Status.PENDING)

    def test_repeated_create_returns_existing_payment(self):
        self.client.force_authenticate(user=self.customer)
        payload = {"appointment_id": str(self.appointment.id)}

        first_response = self.client.post(
            self.create_url(),
            payload,
            HTTP_IDEMPOTENCY_KEY="api-repeat-key",
            format="json",
        )
        second_response = self.client.post(
            self.create_url(),
            payload,
            HTTP_IDEMPOTENCY_KEY="api-repeat-key",
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.data["id"], first_response.data["id"])

    def test_user_retrieves_own_payment(self):
        payment, _ = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "api-detail-key",
        )
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(self.detail_url(payment))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(payment.id))

    def test_user_cannot_retrieve_other_customer_payment(self):
        payment, _ = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "api-other-detail-key",
        )
        self.client.force_authenticate(user=self.other_customer)

        response = self.client.get(self.detail_url(payment))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

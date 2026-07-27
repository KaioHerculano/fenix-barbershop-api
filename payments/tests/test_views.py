from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from payments.models import Payment
from payments.services import create_payment_for_appointment
from payments.tests.factories import FakeData
from scheduling.models import Appointment


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
        self.assertEqual(response.data["payment_method"], Payment.Method.PIX)
        self.assertTrue(response.data["payment_code"])

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

    def test_public_webhook_confirms_payment(self):
        payment, _ = create_payment_for_appointment(
            self.customer,
            self.appointment.id,
            "api-webhook-key",
        )

        response = self.client.post(
            reverse("payment-webhook"),
            {
                "id": "api-event-1",
                "provider_payment_id": payment.provider_payment_id,
                "status": "paid",
                "type": "payment",
                "action": "payment.updated",
            },
            format="json",
        )

        payment.refresh_from_db()
        self.appointment.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertEqual(self.appointment.status, Appointment.Status.CONFIRMED)

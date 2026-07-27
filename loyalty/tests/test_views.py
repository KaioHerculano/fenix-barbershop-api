from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from loyalty.models import LoyaltyCard, LoyaltyTransaction
from loyalty.tests.factories import FakeData
from scheduling.models import Appointment


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

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from barbers.models import BarberService
from company.models import Company, CompanyEmployee, StaffInvitation
from company.services import accept_staff_invitation, create_staff_invitation
from services.models import Service


class FakeData:
    def email(self):
        return f"{get_random_string(10).lower()}@example.com"

    def password(self):
        return "StrongPass123!"

    def user(self, full_name=None, email=None):
        value = get_random_string(8)
        return User.objects.create_user(
            email=email or self.email(),
            full_name=full_name or f"Pessoa {value}",
            password=self.password(),
        )

    def company(self):
        value = get_random_string(8).lower()
        return Company.objects.create(
            name=f"Barbearia {value}",
            slug=f"barbearia-{value}",
        )

    def owner(self, company):
        user = self.user()
        CompanyEmployee.objects.create(
            user=user,
            company=company,
            role=User.Role.OWNER,
            is_active=True,
        )
        return user

    def service(self, company):
        value = get_random_string(8)
        return Service.objects.create(
            company=company,
            name=f"Servico {value}",
            price=Decimal("50.00"),
            duration_minutes=30,
            is_active=True,
        )


class StaffInvitationModelTests(TestCase):
    def test_generates_token_and_digest(self):
        token, digest = StaffInvitation.build_token()

        self.assertNotEqual(token, digest)
        self.assertEqual(StaffInvitation.digest_token(token), digest)
        self.assertEqual(len(digest), 64)


class StaffInvitationServiceTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.owner = self.fake.owner(self.company)
        self.service = self.fake.service(self.company)
        self.invitation_task = patch(
            "notifications.tasks.send_staff_invitation_email.delay"
        ).start()
        self.welcome_task = patch(
            "notifications.tasks.send_welcome_email.delay"
        ).start()
        self.addCleanup(patch.stopall)

    def test_creates_staff_invitation_with_services(self):
        invitation = create_staff_invitation(
            self.company,
            self.owner,
            {
                "email": self.fake.email(),
                "full_name": "Barbeiro Convite",
                "service_ids": [self.service.id],
            },
        )

        self.assertEqual(invitation.role, User.Role.BARBER)
        self.assertEqual(list(invitation.services.all()), [self.service])
        self.assertTrue(hasattr(invitation, "raw_token"))

    def test_rejects_duplicate_pending_invitation(self):
        email = self.fake.email()
        create_staff_invitation(
            self.company,
            self.owner,
            {"email": email, "service_ids": []},
        )

        with self.assertRaises(Exception):
            create_staff_invitation(
                self.company,
                self.owner,
                {"email": email, "service_ids": []},
            )

    def test_accepts_invitation_creating_user_employee_and_services(self):
        invitation = create_staff_invitation(
            self.company,
            self.owner,
            {
                "email": self.fake.email(),
                "full_name": "Novo Barbeiro",
                "service_ids": [self.service.id],
            },
        )

        employee = accept_staff_invitation(
            invitation.raw_token,
            type("Anonymous", (), {"is_authenticated": False})(),
            {
                "full_name": "Novo Barbeiro",
                "password": self.fake.password(),
                "password_confirmation": self.fake.password(),
            },
        )

        invitation.refresh_from_db()
        self.assertEqual(employee.role, User.Role.BARBER)
        self.assertTrue(employee.is_active)
        self.assertTrue(invitation.is_accepted)
        self.assertTrue(
            BarberService.objects.filter(
                barber=employee,
                service=self.service,
                is_active=True,
            ).exists()
        )

    def test_rejects_expired_invitation(self):
        invitation = create_staff_invitation(
            self.company,
            self.owner,
            {"email": self.fake.email(), "service_ids": []},
        )
        invitation.expires_at = timezone.now() - timedelta(minutes=1)
        invitation.save(update_fields=["expires_at"])

        with self.assertRaises(Exception):
            accept_staff_invitation(
                invitation.raw_token,
                type("Anonymous", (), {"is_authenticated": False})(),
                {
                    "full_name": "Novo Barbeiro",
                    "password": self.fake.password(),
                    "password_confirmation": self.fake.password(),
                },
            )


class StaffInvitationAPITests(APITestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.owner = self.fake.owner(self.company)
        self.service = self.fake.service(self.company)
        self.invitation_task = patch(
            "notifications.tasks.send_staff_invitation_email.delay"
        ).start()
        self.welcome_task = patch(
            "notifications.tasks.send_welcome_email.delay"
        ).start()
        self.addCleanup(patch.stopall)

    def create_url(self):
        return reverse(
            "company-staff-invitation-create",
            kwargs={"company_slug": self.company.slug},
        )

    def detail_url(self, token):
        return reverse("staff-invitation-detail", kwargs={"token": token})

    def accept_url(self, token):
        return reverse("staff-invitation-accept", kwargs={"token": token})

    def test_owner_creates_staff_invitation(self):
        self.client.force_authenticate(user=self.owner)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                self.create_url(),
                {
                    "email": self.fake.email(),
                    "full_name": "Barbeiro API",
                    "service_ids": [str(self.service.id)],
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("token_digest", response.data)
        self.invitation_task.assert_called_once()

    def test_non_owner_cannot_create_staff_invitation(self):
        self.client.force_authenticate(user=self.fake.user())

        response = self.client.post(
            self.create_url(),
            {"email": self.fake.email(), "service_ids": []},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rejects_invalid_service_for_invitation(self):
        other_company = self.fake.company()
        other_service = self.fake.service(other_company)
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            self.create_url(),
            {
                "email": self.fake.email(),
                "service_ids": [str(other_service.id)],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_detail_returns_invitation(self):
        invitation = create_staff_invitation(
            self.company,
            self.owner,
            {"email": self.fake.email(), "service_ids": [self.service.id]},
        )

        response = self.client.get(self.detail_url(invitation.raw_token))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], invitation.email)
        self.assertNotIn("token_digest", response.data)

    def test_accept_invitation_creates_new_barber(self):
        invitation = create_staff_invitation(
            self.company,
            self.owner,
            {"email": self.fake.email(), "service_ids": [self.service.id]},
        )

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                self.accept_url(invitation.raw_token),
                {
                    "full_name": "Aceite Barbeiro",
                    "password": self.fake.password(),
                    "password_confirmation": self.fake.password(),
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], User.Role.BARBER)
        self.welcome_task.assert_called_once()

    def test_existing_user_must_authenticate_to_accept(self):
        existing_user = self.fake.user(email=self.fake.email())
        invitation = create_staff_invitation(
            self.company,
            self.owner,
            {"email": existing_user.email, "service_ids": []},
        )

        response = self.client.post(
            self.accept_url(invitation.raw_token), {}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_invited_user_accepts_invitation(self):
        user = self.fake.user(email=self.fake.email())
        invitation = create_staff_invitation(
            self.company,
            self.owner,
            {"email": user.email, "service_ids": []},
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(
            self.accept_url(invitation.raw_token), {}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            CompanyEmployee.objects.filter(
                user=user,
                company=self.company,
                role=User.Role.BARBER,
                is_active=True,
            ).exists()
        )

    def test_authenticated_wrong_user_cannot_accept_invitation(self):
        invitation = create_staff_invitation(
            self.company,
            self.owner,
            {"email": self.fake.email(), "service_ids": []},
        )
        self.client.force_authenticate(user=self.fake.user())

        response = self.client.post(
            self.accept_url(invitation.raw_token), {}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

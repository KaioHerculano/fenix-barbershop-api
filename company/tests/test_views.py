from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from company.models import CompanyEmployee
from company.services import create_staff_invitation
from company.tests.factories import FakeData


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

    @override_settings(DEBUG=True)
    @patch.dict(
        "os.environ",
        {"FRONTEND_URL": "http://localhost:3000", "RESEND_API_KEY": ""},
    )
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
        self.assertTrue(
            response.data["dev_invitation_url"].startswith(
                "http://localhost:3000/invitations/"
            )
        )
        self.invitation_task.assert_called_once()

    @override_settings(DEBUG=True)
    @patch.dict(
        "os.environ",
        {"FRONTEND_URL": "http://localhost:3000", "RESEND_API_KEY": "secret"},
    )
    def test_owner_create_invitation_hides_dev_url_when_email_provider_is_configured(
        self,
    ):
        self.client.force_authenticate(user=self.owner)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                self.create_url(),
                {
                    "email": self.fake.email(),
                    "service_ids": [str(self.service.id)],
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["dev_invitation_url"])

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

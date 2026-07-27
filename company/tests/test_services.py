from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from barbers.models import BarberService
from company.services import accept_staff_invitation, create_staff_invitation
from company.tests.factories import FakeData


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

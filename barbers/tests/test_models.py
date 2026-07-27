from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import User
from barbers.models import BarberService
from barbers.tests.factories import FakeData


class BarberServiceModelTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()

    def test_create_valid_barber_service_assignment(self):
        barber = self.fake.employee(self.company)
        service = self.fake.service(self.company)

        assignment = BarberService.objects.create(barber=barber, service=service)

        self.assertEqual(assignment.barber, barber)
        self.assertEqual(assignment.service, service)
        self.assertTrue(assignment.is_active)

    def test_rejects_assignment_for_non_barber_employee(self):
        owner = self.fake.employee(self.company, role=User.Role.OWNER)
        service = self.fake.service(self.company)

        assignment = BarberService(barber=owner, service=service)

        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_rejects_assignment_between_different_companies(self):
        barber = self.fake.employee(self.company)
        other_company = self.fake.company()
        service = self.fake.service(other_company)

        assignment = BarberService(barber=barber, service=service)

        with self.assertRaises(ValidationError):
            assignment.full_clean()

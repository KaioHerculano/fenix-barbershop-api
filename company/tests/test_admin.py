from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from accounts.models import User
from company.admin import CompanyEmployeeAdmin
from company.models import CompanyEmployee
from company.tests.factories import FakeData


class CompanyEmployeeAdminTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.user = self.fake.user()
        self.admin = CompanyEmployeeAdmin(CompanyEmployee, AdminSite())
        self.request = RequestFactory().get("/")

    def test_deactivate_employees_action(self):
        employee = CompanyEmployee.objects.create(
            company=self.company,
            user=self.user,
            role=User.Role.BARBER,
            is_active=True,
        )

        self.admin.deactivate_employees(
            self.request,
            CompanyEmployee.objects.filter(id=employee.id),
        )

        employee.refresh_from_db()
        self.assertFalse(employee.is_active)

    def test_activate_employees_action(self):
        employee = CompanyEmployee.objects.create(
            company=self.company,
            user=self.user,
            role=User.Role.BARBER,
            is_active=False,
        )

        self.admin.activate_employees(
            self.request,
            CompanyEmployee.objects.filter(id=employee.id),
        )

        employee.refresh_from_db()
        self.assertTrue(employee.is_active)

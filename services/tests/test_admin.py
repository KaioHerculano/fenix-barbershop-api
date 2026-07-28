from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from services.admin import ServiceAdmin
from services.models import Service
from services.tests.factories import FakeData


class ServiceAdminTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.admin = ServiceAdmin(Service, AdminSite())
        self.request = RequestFactory().get("/")

    def test_deactivate_services_action(self):
        service = self.fake.service(self.company, is_active=True)

        self.admin.deactivate_services(
            self.request,
            Service.objects.filter(id=service.id),
        )

        service.refresh_from_db()
        self.assertFalse(service.is_active)

    def test_activate_services_action(self):
        service = self.fake.service(self.company, is_active=False)

        self.admin.activate_services(
            self.request,
            Service.objects.filter(id=service.id),
        )

        service.refresh_from_db()
        self.assertTrue(service.is_active)

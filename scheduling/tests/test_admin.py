from datetime import time
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase
from django.utils import timezone

from loyalty.models import LoyaltyCard, LoyaltyTransaction
from payments.models import Payment
from scheduling.admin import AppointmentAdmin, AppointmentDateListFilter
from scheduling.models import Appointment
from scheduling.tests.factories import FakeData


class AppointmentAdminTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.customer = self.fake.user()
        self.barber = self.fake.barber(self.company)
        self.service = self.fake.service(self.company, duration_minutes=30)
        self.fake.assignment(self.barber, self.service)
        self.appointment_date = self.fake.future_date()
        self.admin = AppointmentAdmin(Appointment, AdminSite())
        self.request = RequestFactory().get("/")
        self.admin.message_user = patch.object(self.admin, "message_user").start()
        self.cancelled_task = patch(
            "scheduling.services.send_appointment_cancelled_email.delay"
        ).start()
        self.addCleanup(patch.stopall)

    def test_cancel_action_cancels_pending_payment(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            self.appointment_date,
            status=Appointment.Status.PENDING,
        )
        payment = Payment.objects.create(
            user=self.customer,
            appointment=appointment,
            amount=self.service.price,
            status=Payment.Status.PENDING,
            idempotency_key="admin-cancel-payment",
        )

        self.admin.cancel_selected_appointments(
            self.request,
            Appointment.objects.filter(id=appointment.id),
        )

        appointment.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CANCELLED)
        self.assertEqual(payment.status, Payment.Status.CANCELLED)

    def test_complete_action_completes_appointment_and_awards_points(self):
        appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            self.appointment_date,
            status=Appointment.Status.CONFIRMED,
        )

        self.admin.complete_selected_appointments(
            self.request,
            Appointment.objects.filter(id=appointment.id),
        )

        appointment.refresh_from_db()
        card = LoyaltyCard.objects.get(company=self.company, user=self.customer)
        transaction = LoyaltyTransaction.objects.get(appointment=appointment)
        self.assertEqual(appointment.status, Appointment.Status.COMPLETED)
        self.assertEqual(card.points_balance, 1)
        self.assertEqual(transaction.type, LoyaltyTransaction.Type.EARN)

    def test_date_filter_returns_today_appointments(self):
        today_appointment = self.fake.appointment(
            self.company,
            self.customer,
            self.barber,
            self.service,
            timezone.localdate(),
            start_time=time(9, 0),
        )
        self.fake.appointment(
            self.company,
            self.fake.user(),
            self.barber,
            self.service,
            self.fake.future_date(),
            start_time=time(10, 0),
        )
        request = RequestFactory().get("/", {"period": "today"})
        list_filter = AppointmentDateListFilter(
            request,
            {"period": "today"},
            Appointment,
            self.admin,
        )
        list_filter.used_parameters = {"period": "today"}

        queryset = list_filter.queryset(request, Appointment.objects.all())

        self.assertEqual(list(queryset), [today_appointment])

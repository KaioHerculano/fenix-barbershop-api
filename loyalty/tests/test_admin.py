from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from loyalty.admin import LoyaltyTransactionAdmin
from loyalty.models import LoyaltyCard, LoyaltyTransaction
from loyalty.tests.factories import FakeData


class LoyaltyTransactionAdminTests(TestCase):
    def setUp(self):
        self.fake = FakeData()
        self.company = self.fake.company()
        self.user = self.fake.user()
        self.admin = LoyaltyTransactionAdmin(LoyaltyTransaction, AdminSite())
        self.request = RequestFactory().get("/")

    def test_save_model_creates_adjustment_transaction(self):
        transaction = LoyaltyTransaction(
            company=self.company,
            user=self.user,
            points=3,
            description="Ajuste operacional",
        )

        self.admin.save_model(self.request, transaction, form=None, change=False)

        card = LoyaltyCard.objects.get(company=self.company, user=self.user)
        transaction.refresh_from_db()
        self.assertEqual(card.points_balance, 3)
        self.assertEqual(transaction.type, LoyaltyTransaction.Type.ADJUSTMENT)
        self.assertEqual(transaction.points, 3)

    def test_save_model_rejects_negative_balance_adjustment(self):
        transaction = LoyaltyTransaction(
            company=self.company,
            user=self.user,
            points=-1,
            description="Ajuste invalido",
        )

        with self.assertRaises(Exception):
            self.admin.save_model(self.request, transaction, form=None, change=False)

        self.assertFalse(
            LoyaltyCard.objects.filter(company=self.company, user=self.user).exists()
        )

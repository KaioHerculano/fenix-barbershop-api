from django.urls import path

from loyalty.views import LoyaltyMeView, LoyaltyRedeemView, LoyaltyTransactionListView

urlpatterns = [
    path("api/v1/loyalty/me/", LoyaltyMeView.as_view(), name="loyalty-me"),
    path(
        "api/v1/loyalty/transactions/",
        LoyaltyTransactionListView.as_view(),
        name="loyalty-transaction-list",
    ),
    path(
        "api/v1/loyalty/redeem/",
        LoyaltyRedeemView.as_view(),
        name="loyalty-redeem",
    ),
]

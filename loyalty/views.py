from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.schemas.loyalty import (
    loyalty_me_schema,
    loyalty_redeem_schema,
    loyalty_transactions_schema,
)
from loyalty.selectors import (
    get_active_company_by_slug,
    get_user_loyalty_summary,
    get_user_loyalty_transactions,
    get_user_points_totals,
)
from loyalty.serializers import (
    LoyaltyRedeemSerializer,
    LoyaltySummarySerializer,
    LoyaltyTransactionSerializer,
)
from loyalty.services import redeem_points


class LoyaltyMeView(APIView):
    permission_classes = [IsAuthenticated]

    @loyalty_me_schema
    def get(self, request):
        company_slug = request.query_params.get("company_slug")
        summary = get_user_loyalty_summary(request.user, company_slug)
        summary.update(get_user_points_totals(request.user, company_slug))
        return Response(LoyaltySummarySerializer(summary).data)


class LoyaltyTransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    @loyalty_transactions_schema
    def get(self, request):
        company_slug = request.query_params.get("company_slug")
        transactions = get_user_loyalty_transactions(request.user, company_slug)
        serializer = LoyaltyTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class LoyaltyRedeemView(APIView):
    permission_classes = [IsAuthenticated]

    @loyalty_redeem_schema
    def post(self, request):
        serializer = LoyaltyRedeemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = get_active_company_by_slug(serializer.validated_data["company_slug"])
        loyalty_transaction = redeem_points(
            request.user,
            company,
            serializer.validated_data["points"],
            serializer.validated_data.get("description", "Resgate de pontos"),
        )
        response_serializer = LoyaltyTransactionSerializer(loyalty_transaction)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

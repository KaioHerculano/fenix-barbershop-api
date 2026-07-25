from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.schemas.payments import payment_create_schema, payment_detail_schema
from payments.selectors import get_user_payment
from payments.serializers import PaymentCreateSerializer, PaymentSerializer
from payments.services import create_payment_for_appointment


class PaymentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @payment_create_schema
    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment, created = create_payment_for_appointment(
            request.user,
            serializer.validated_data["appointment_id"],
            request.headers.get("Idempotency-Key"),
        )
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(PaymentSerializer(payment).data, status=response_status)


class PaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @payment_detail_schema
    def get(self, request, payment_id):
        payment = get_user_payment(request.user, payment_id)
        return Response(PaymentSerializer(payment).data)

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.serializers import (
    CustomerRegistrationSerializer,
    OwnerRegistrationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserMeSerializer,
    UserMeUpdateSerializer,
)
from accounts.services import CustomerRegistrationService, PasswordResetService
from app.schemas.accounts import (
    customer_registration_schema,
    owner_registration_schema,
    password_reset_confirm_schema,
    password_reset_request_schema,
    token_obtain_pair_schema,
    token_refresh_schema,
    user_me_schema,
)


class LoginView(TokenObtainPairView):
    @token_obtain_pair_schema
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenRefreshDocumentedView(TokenRefreshView):
    @token_refresh_schema
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class OwnerRegistrationView(APIView):
    permission_classes = [AllowAny]

    @owner_registration_schema
    def post(self, request):
        serializer = OwnerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Owner and Company created sucessfully."},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerRegistrationView(APIView):
    permission_classes = [AllowAny]

    @customer_registration_schema
    def post(self, request):
        serializer = CustomerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            CustomerRegistrationService.register_customer(
                email=serializer.validated_data["email"],
                full_name=serializer.validated_data["full_name"],
                phone=serializer.validated_data.get("phone", ""),
                password=serializer.validated_data["password"],
            )
            return Response(
                {"message": "Customer created successfully."},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    @user_me_schema
    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)

    @user_me_schema
    def patch(self, request):
        serializer = UserMeUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @password_reset_request_schema
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            PasswordResetService.request_reset(email=serializer.validated_data["email"])
            return Response(
                {"message": "Se o e-mail existir, um link foi enviado."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @password_reset_confirm_schema
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            success = PasswordResetService.confirm_reset(
                uidb64=serializer.validated_data["uidb64"],
                token=serializer.validated_data["token"],
                new_password=serializer.validated_data["new_password"],
            )
            if success:
                return Response(
                    {"message": "Senha redefinida com sucesso."},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": "Token ou usuário inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

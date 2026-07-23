from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.schemas.company import (
    staff_invitation_accept_schema,
    staff_invitation_create_schema,
    staff_invitation_detail_schema,
)
from company.models import Company, StaffInvitation
from company.serializers import (
    StaffInvitationAcceptResponseSerializer,
    StaffInvitationAcceptSerializer,
    StaffInvitationCreateSerializer,
    StaffInvitationSerializer,
)
from company.services import (
    accept_staff_invitation,
    create_staff_invitation,
    get_invitation_by_token,
    user_is_company_owner,
)


class StaffInvitationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @staff_invitation_create_schema
    def post(self, request, company_slug):
        company = get_object_or_404(Company, slug=company_slug, is_active=True)
        if not user_is_company_owner(request.user, company):
            raise PermissionDenied("Usuario nao pode convidar barbeiros nesta empresa.")

        serializer = StaffInvitationCreateSerializer(
            data=request.data,
            context={"company": company},
        )
        serializer.is_valid(raise_exception=True)
        invitation = create_staff_invitation(
            company,
            request.user,
            serializer.validated_data,
        )
        return Response(
            StaffInvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED,
        )


class StaffInvitationDetailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @staff_invitation_detail_schema
    def get(self, request, token):
        invitation = get_object_or_404(
            StaffInvitation.objects.select_related("company").prefetch_related(
                "services"
            ),
            token_digest=StaffInvitation.digest_token(token),
        )
        return Response(StaffInvitationSerializer(invitation).data)


class StaffInvitationAcceptView(APIView):
    permission_classes = [AllowAny]

    @staff_invitation_accept_schema
    def post(self, request, token):
        serializer = StaffInvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = get_invitation_by_token(token)
        employee = accept_staff_invitation(
            token,
            request.user,
            serializer.validated_data,
        )
        response = {
            "company_slug": invitation.company.slug,
            "role": employee.role,
            "is_active": employee.is_active,
        }
        return Response(StaffInvitationAcceptResponseSerializer(response).data)

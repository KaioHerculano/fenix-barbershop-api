from django.db import transaction
from rest_framework import serializers

from accounts.models import User
from app.exceptions import ConflictError
from company.models import Company, CompanyEmployee


class OwnerRegistrationSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=255)
    company_slug = serializers.SlugField(max_length=100)

    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise ConflictError("This email is already in use")
        return value

    def validate_company_slug(self, value):
        if Company.objects.filter(slug=value).exists():
            raise ConflictError("This company slug is already in use")
        return value

    def create(self, validated_data):
        with transaction.atomic():
            company = Company.objects.create(
                name=validated_data["company_name"], slug=validated_data["company_slug"]
            )
            user = User.objects.create_user(
                email=validated_data["email"],
                full_name=validated_data["full_name"],
                password=validated_data["password"],
            )
            CompanyEmployee.objects.create(
                user=user, company=company, role=User.Role.OWNER
            )
            return user

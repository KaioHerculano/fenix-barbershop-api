from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
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

    def validate(self, data):
        password = data.get("password")
        if password:
            try:
                validate_password(password, user=None)
            except DjangoValidationError as e:
                raise serializers.ValidationError({"password": list(e.messages)})
        return data

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


class CustomerRegistrationSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise ConflictError("This email is already in use")
        return value

    def validate(self, data):
        password = data.get("password")
        password_confirmation = data.get("password_confirmation")

        if password != password_confirmation:
            raise serializers.ValidationError(
                {"password_confirmation": "As senhas não coincidem."}
            )

        if password:
            try:
                validate_password(password, user=None)
            except DjangoValidationError as e:
                raise serializers.ValidationError({"password": list(e.messages)})

        return data


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "phone"]


class UserMeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "phone"]


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    new_password_confirmation = serializers.CharField(write_only=True)

    def validate(self, data):
        new_password = data.get("new_password")
        new_password_confirmation = data.get("new_password_confirmation")

        if new_password != new_password_confirmation:
            raise serializers.ValidationError(
                {"new_password_confirmation": "As senhas não coincidem."}
            )

        if new_password:
            try:
                validate_password(new_password, user=None)
            except DjangoValidationError as e:
                raise serializers.ValidationError({"new_password": list(e.messages)})

        return data

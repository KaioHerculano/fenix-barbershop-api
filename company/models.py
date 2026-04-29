from django.db import models

from accounts.models import User


class Company(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=100)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.name


class CompanyEmployee(models.Model):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
    )
    company = models.ForeignKey(
        "company.Company",
        on_delete=models.CASCADE,
    )
    role = models.CharField(max_length=20, choices=User.Role.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "company")

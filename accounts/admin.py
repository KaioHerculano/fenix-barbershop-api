from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from accounts.models import CustomerProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = (
        "email",
        "full_name",
        "phone",
        "is_active",
        "is_staff",
        "date_joined",
    )
    search_fields = ("email", "full_name", "phone")
    list_filter = ("is_active", "is_staff", "is_superuser", "date_joined")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "updated_at", "last_login")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dados pessoais", {"fields": ("full_name", "phone")}),
        (
            "Permissoes",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Datas", {"fields": ("last_login", "date_joined", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "phone",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "birth_date")
    search_fields = ("user__email", "user__full_name", "user__phone")
    list_filter = ("birth_date",)
    autocomplete_fields = ("user",)

from django.contrib import admin

from company.models import Company, CompanyEmployee, StaffInvitation


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "is_active", "created_at")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)


@admin.register(CompanyEmployee)
class CompanyEmployeeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "company", "role", "is_active", "created_at")
    search_fields = ("user__email", "company__name")
    list_filter = ("company", "role", "is_active")


@admin.register(StaffInvitation)
class StaffInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "company",
        "email",
        "role",
        "invited_by",
        "accepted_by",
        "expires_at",
        "accepted_at",
    )
    search_fields = ("email", "company__name", "company__slug")
    list_filter = ("company", "role", "accepted_at", "expires_at")
    readonly_fields = ("token_digest", "created_at", "updated_at", "accepted_at")

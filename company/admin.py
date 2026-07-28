from django.contrib import admin

from company.models import Company, CompanyEmployee, StaffInvitation


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "phone", "is_active", "created_at")
    search_fields = ("name", "slug", "phone")
    list_filter = ("is_active", "created_at")
    ordering = ("name",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(CompanyEmployee)
class CompanyEmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "employee_name",
        "employee_email",
        "company",
        "role",
        "is_active",
        "created_at",
    )
    search_fields = (
        "user__email",
        "user__full_name",
        "user__phone",
        "company__name",
        "company__slug",
    )
    list_filter = ("company", "role", "is_active", "created_at")
    ordering = ("company__name", "user__full_name")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("user", "company")
    actions = ("activate_employees", "deactivate_employees")

    @admin.display(description="Nome")
    def employee_name(self, obj):
        return obj.user.full_name

    @admin.display(description="Email")
    def employee_email(self, obj):
        return obj.user.email

    @admin.action(description="Ativar funcionarios selecionados")
    def activate_employees(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Desativar funcionarios selecionados")
    def deactivate_employees(self, request, queryset):
        queryset.update(is_active=False)


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
    search_fields = (
        "email",
        "full_name",
        "company__name",
        "company__slug",
        "invited_by__email",
        "accepted_by__email",
    )
    list_filter = ("company", "role", "accepted_at", "expires_at", "created_at")
    readonly_fields = ("id", "token_digest", "created_at", "updated_at", "accepted_at")
    autocomplete_fields = ("company", "services", "invited_by", "accepted_by")
    ordering = ("-created_at",)

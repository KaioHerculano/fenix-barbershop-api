from django.contrib import admin

from company.models import Company, CompanyEmployee


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "is_active", "created_at")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)


@admin.register(CompanyEmployee)
class CompanyEmployeeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "company", "role", "created_at")
    search_fields = ("user__email", "company__name")
    list_filter = ("role",)

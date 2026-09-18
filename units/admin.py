from django.contrib import admin

from units.models import OwnershipHistory, TenancyHistory, Unit


class OwnershipInline(admin.TabularInline):
    model = OwnershipHistory
    extra = 0


class TenancyInline(admin.TabularInline):
    model = TenancyHistory
    extra = 0


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("number", "owner_name", "owner_phone", "tenant_name", "user")
    inlines = [OwnershipInline, TenancyInline]

from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import PaymentRecord

@admin.action(description="Mark selected payments as Verified")
def mark_as_verified(modeladmin, request, queryset):
    for record in queryset:
        record.payment_status = 'verified'
        record.save()
        if record.registration:
            record.registration.payment_status = 'VERIFIED'
            record.registration.save()

@admin.action(description="Mark selected payments as Rejected")
def mark_as_rejected(modeladmin, request, queryset):
    for record in queryset:
        record.payment_status = 'rejected'
        record.save()
        if record.registration:
            record.registration.payment_status = 'REJECTED'
            record.registration.save()

from django.utils.html import format_html

@admin.register(PaymentRecord)
class PaymentRecordAdmin(ModelAdmin):
    list_display = ('registration_info', 'amount', 'payment_status', 'reference_id', 'transaction_id', 'screenshot_preview', 'created_at')
    list_filter = ('payment_status',)
    search_fields = ('reference_id', 'transaction_id', 'registration__email', 'registration__name')
    readonly_fields = ('created_at', 'updated_at')
    actions = [mark_as_verified, mark_as_rejected]

    def screenshot_preview(self, obj):
        if obj.screenshot:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" width="50" height="50" /></a>', obj.screenshot.url)
        return "No Screenshot"
    screenshot_preview.short_description = 'Screenshot'

    def registration_info(self, obj):
        return f"{obj.registration.id} - {obj.registration.name} ({obj.registration.email})"
    registration_info.short_description = 'Registration'

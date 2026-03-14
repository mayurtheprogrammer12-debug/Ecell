import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from .models import PaymentRecord

def export_payments_as_csv(modeladmin, request, queryset):
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={meta}_export.csv'
    writer = csv.writer(response)

    # Custom header to include the Screenshot URL column name
    writer.writerow(field_names + ['screenshot_url'])
    
    for obj in queryset:
        row = [getattr(obj, field) for field in field_names]
        
        # Add the full URL for the screenshot if it exists
        screenshot_url = ""
        if obj.screenshot:
            screenshot_url = request.build_absolute_uri(obj.screenshot.url)
        
        row.append(screenshot_url)
        writer.writerow(row)

    return response

export_payments_as_csv.short_description = "🚀 Export Selected to Excel (CSV)"

@admin.register(PaymentRecord)
class PaymentRecordAdmin(ModelAdmin):
    list_display = (
        'participant_name', 'amount', 'payment_status', 
        'transaction_id', 'screenshot_preview', 'created_at'
    )
    list_filter = ('payment_status', 'created_at')
    search_fields = ('registration__name', 'registration__email', 'transaction_id', 'reference_id')
    actions = [export_payments_as_csv]
    
    def screenshot_preview(self, obj):
        if obj.screenshot:
             try:
                 return format_html('<a href="{}" target="_blank"><img src="{}" style="max-height: 50px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); shadow: 0 4px 6px rgba(0,0,0,0.1);"/></a>', obj.screenshot.url, obj.screenshot.url)
             except Exception:
                 return "Error Loading Image"
        return "No Screenshot"
    screenshot_preview.short_description = "Receipt Preview"
    
    def participant_name(self, obj):
        return obj.registration.name
    participant_name.short_description = "Participant"

    readonly_fields = ('created_at',)
    
    fieldsets = (
        ("Basic Info", {
            "fields": ("registration", "amount", "payment_status", "created_at")
        }),
        ("Transaction Details", {
            "fields": ("transaction_id", "reference_id", "screenshot")
        }),
    )

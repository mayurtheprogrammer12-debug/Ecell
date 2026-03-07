import csv
from django.contrib import admin
from django.http import HttpResponse
from unfold.admin import ModelAdmin
from .models import PaymentRecord

def export_payments_as_csv(modeladmin, request, queryset):
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={meta}_export.csv'
    writer = csv.writer(response)

    writer.writerow(field_names)
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])

    return response

export_payments_as_csv.short_description = "🚀 Export Selected to Excel (CSV)"

@admin.register(PaymentRecord)
class PaymentRecordAdmin(ModelAdmin):
    list_display = (
        'participant_name', 'amount', 'payment_status', 
        'transaction_id', 'reference_id', 'created_at'
    )
    list_filter = ('payment_status', 'created_at')
    search_fields = ('registration__name', 'registration__email', 'transaction_id', 'reference_id')
    actions = [export_payments_as_csv]
    
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

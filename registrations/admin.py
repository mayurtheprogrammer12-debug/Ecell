import csv
from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Q, Sum, Count
from unfold.admin import ModelAdmin
from .models import UserRegistration, FreeEntryWhitelist, AttendanceSession, AttendanceRecord, EventSettings, ReferralCode

# --- FILTERS ---

class CollegeDomainFilter(admin.SimpleListFilter):
    title = 'College Domain'
    parameter_name = 'college_domain'

    def lookups(self, request, model_admin):
        return (
            ('PCCOE', 'PCCOE (@pccoepune.org)'),
            ('External', 'External Domain'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'PCCOE':
            return queryset.filter(email__endswith='@pccoepune.org')
        if self.value() == 'External':
            return queryset.exclude(email__endswith='@pccoepune.org')
        return queryset

class IsFreeEligibleFilter(admin.SimpleListFilter):
    title = 'Is Free Eligible (Whitelisted/PCCOE)'
    parameter_name = 'is_free_eligible'

    def lookups(self, request, model_admin):
        return (
            ('Yes', 'Yes (Free)'),
            ('No', 'No (Paid)'),
        )

    def queryset(self, request, queryset):
        whitelisted_domains = FreeEntryWhitelist.objects.filter(whitelist_type='DOMAIN').values_list('value', flat=True)
        whitelisted_emails = FreeEntryWhitelist.objects.filter(whitelist_type='EMAIL').values_list('value', flat=True)

        if self.value() == 'Yes':
            q = Q(email__endswith='@pccoepune.org') | Q(email__in=whitelisted_emails)
            for domain in whitelisted_domains:
                q |= Q(email__endswith='@' + domain)
            return queryset.filter(q)
            
        if self.value() == 'No':
            q = Q(email__endswith='@pccoepune.org') | Q(email__in=whitelisted_emails)
            for domain in whitelisted_domains:
                q |= Q(email__endswith='@' + domain)
            return queryset.exclude(q)
            
        return queryset

# --- ACTIONS ---

def export_as_csv(modeladmin, request, queryset):
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={meta}.csv'
    writer = csv.writer(response)

    writer.writerow(field_names)
    for obj in queryset:
        row = []
        for field in field_names:
            val = getattr(obj, field)
            if hasattr(val, 'pk'):
                val = str(val)
            row.append(val)
        writer.writerow(row)

    return response

export_as_csv.short_description = "🚀 Export Selected to CSV"

def mark_round2_qualified(modeladmin, request, queryset):
    queryset.update(selected_for_round2=True, round2_unlocked=True)
mark_round2_qualified.short_description = "✅ Qualify for Round 2"

def verify_payments_bulk(modeladmin, request, queryset):
    queryset.update(payment_status='VERIFIED')
verify_payments_bulk.short_description = "💰 Verify Payments"

def mark_attendance_present_bulk(modeladmin, request, queryset):
    try:
        latest_session = AttendanceSession.objects.filter(is_active=True).latest('created_at')
        for reg in queryset:
            AttendanceRecord.objects.get_or_create(
                participant=reg,
                session=latest_session,
                defaults={'status': 'PRESENT'}
            )
    except AttendanceSession.DoesNotExist:
        pass
mark_attendance_present_bulk.short_description = "📍 Mark Attendance (Active Session)"

# --- ADMIN CLASSES ---

@admin.register(UserRegistration)
class UserRegistrationAdmin(ModelAdmin):
    list_display = (
        'name', 'email', 'phone', 'college', 'registration_type', 
        'payment_status', 'final_price', 'referral_code_used', 
        'round1_completed', 'selected_for_round2', 'created_at'
    )
    
    list_filter = (
        CollegeDomainFilter,
        'registration_type', 'payment_status', 'round1_completed', 
        'selected_for_round2', 'referral_code_used', 'created_at', 
        IsFreeEligibleFilter
    )
    
    search_fields = ('name', 'email', 'phone', 'college', 'referral_code_used__referral_code')
    
    actions = [export_as_csv, mark_round2_qualified, verify_payments_bulk, mark_attendance_present_bulk]
    
    readonly_fields = ('created_at',)

@admin.register(EventSettings)
class EventSettingsAdmin(ModelAdmin):
    list_display = ('event_name', 'is_registration_open', 'round1_name', 'round2_name')

@admin.register(FreeEntryWhitelist)
class FreeEntryWhitelistAdmin(ModelAdmin):
    list_display = ('value', 'whitelist_type', 'description')
    list_filter = ('whitelist_type',)
    search_fields = ('value', 'description')

from .admin_attendance import * # Load attendance from separate file

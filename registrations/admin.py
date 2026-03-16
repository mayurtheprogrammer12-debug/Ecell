import csv
from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Q, Sum, Count
from unfold.admin import ModelAdmin
from .models import (
    UserRegistration, FreeEntryWhitelist, AttendanceSession, AttendanceRecord, 
    EventSettings, ReferralCode, Team, TeamMember, RoundNotification, 
    Round3Submission, RoundTimingSettings
)

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

@admin.action(description="🚀 Export Selected to Excel (CSV)")
def export_as_csv(modeladmin, request, queryset):
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={meta}_export.csv'
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

@admin.action(description="✅ Qualify for Round 2")
def mark_round2_qualified(modeladmin, request, queryset):
    for obj in queryset:
        obj.selected_for_round2 = True
        obj.round2_unlocked = True
        obj.save()

@admin.action(description="💰 Verify Payments")
def verify_payments_bulk(modeladmin, request, queryset):
    queryset.update(payment_status='VERIFIED')

@admin.action(description="📍 Mark Attendance (Active Session)")
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

@admin.action(description="🏆 Qualify for Round 3")
def mark_round3_qualified(modeladmin, request, queryset):
    queryset.update(selected_for_round3=True, round3_unlocked=True)

@admin.action(description="📦 Qualify TEAM for Round 3")
def mark_team_round3_qualified(modeladmin, request, queryset):
    queryset.update(selected_for_round3=True)

# --- ADMIN CLASSES ---

@admin.register(UserRegistration)
class UserRegistrationAdmin(ModelAdmin):
    list_display = (
        'name', 'email', 'phone', 'college', 'registration_type', 
        'payment_status', 'registration_email_sent', 'round2_email_sent', 'round1_completed', 
        'selected_for_round2', 'selected_for_round3', 'created_at'
    )
    
    list_filter = (
        CollegeDomainFilter, 'registration_type', 'payment_status', 
        'round1_completed', 'selected_for_round2', 'selected_for_round3',
        'referral_code_used', 'created_at', IsFreeEligibleFilter
    )
    
    search_fields = ('name', 'email', 'phone', 'college', 'referral_code_used__referral_code', 'idea_title')
    
    actions = [export_as_csv, mark_round2_qualified, mark_round3_qualified, verify_payments_bulk, mark_attendance_present_bulk]
    
    fieldsets = (
        ('IDENTITY', {
            'fields': ('registration_type', 'name', 'email', 'phone', 'gender', 'age', 'college', 'city', 'user')
        }),
        ('PAYMENT', {
            'fields': ('payment_status', 'base_price', 'discount_amount', 'final_price', 'referral_code_used', 'reference_id')
        }),
        ('CORE IDEA (ROUND 1)', {
            'fields': ('idea_title', 'idea_description', 'idea_domain', 'idea_agreement', 'round1_completed', 'round1_submitted_at')
        }),
        ('SELECTION STATUS', {
            'fields': (
                'selected_for_round2', 'round2_unlocked', 'round2_completed',
                'selected_for_round3', 'round3_unlocked', 'round3_completed'
            )
        }),
        ('METADATA', {
            'fields': ('registration_email_sent', 'round2_email_sent', 'created_at',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'round1_submitted_at')


@admin.register(EventSettings)
class EventSettingsAdmin(ModelAdmin):
    list_display = ('event_name', 'is_registration_open', 'round1_name', 'round2_name')

@admin.register(FreeEntryWhitelist)
class FreeEntryWhitelistAdmin(ModelAdmin):
    list_display = ('value', 'whitelist_type', 'description')
    list_filter = ('whitelist_type',)
    search_fields = ('value', 'description')

@admin.register(Team)
class TeamAdmin(ModelAdmin):
    list_display = ('team_id', 'team_name', 'creator', 'status', 'selected_for_round3', 'created_at')
    list_filter = ('status', 'selected_for_round3', 'created_at')
    search_fields = ('team_name', 'team_id', 'creator__name', 'creator__email')
    actions = [export_as_csv, mark_team_round3_qualified]

@admin.register(TeamMember)
class TeamMemberAdmin(ModelAdmin):
    list_display = ('participant', 'team', 'added_at')
    search_fields = ('participant__name', 'team__team_name', 'team__team_id')

@admin.register(RoundNotification)
class RoundNotificationAdmin(ModelAdmin):
    list_display = ('participant', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')

@admin.register(Round3Submission)
class Round3SubmissionAdmin(ModelAdmin):
    list_display = ('team', 'uploaded_by', 'uploaded_at')
    search_fields = ('team__team_name', 'team__team_id', 'uploaded_by__name')

@admin.register(RoundTimingSettings)
class RoundTimingSettingsAdmin(ModelAdmin):
    list_display = ('id', 'team_formation_start', 'team_formation_end', 'ppt_submission_start', 'ppt_submission_end')

from .admin_attendance import * # Load attendance from separate file

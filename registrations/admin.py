import csv
from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Q, Sum, Count
from unfold.admin import ModelAdmin
from .models import (
    UserRegistration, FreeEntryWhitelist, AttendanceSession, 
    AttendanceRecord, EventSettings, ReferralCode, Team, 
    TeamMember, RoundNotification, Round3Submission, RoundTimingSettings
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

export_as_csv.short_description = "🚀 Export Selected to Excel (CSV)"

def mark_round2_qualified(modeladmin, request, queryset):
    for obj in queryset:
        obj.selected_for_round2 = True
        obj.round2_unlocked = True
        obj.save()
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

def mark_round3_qualified(modeladmin, request, queryset):
    queryset.update(selected_for_round3=True, round3_unlocked=True)
mark_round3_qualified.short_description = "🏆 Qualify for Round 3 (Individual)"

def push_round2_selection(modeladmin, request, queryset):
    from .models import RoundNotification
    # Note: Email sending logic would go here. For now focusing on Dashboard Notifications.
    selected_count = 0
    not_selected_count = 0
    
    for reg in queryset:
        if reg.selected_for_round2:
            RoundNotification.objects.create(
                participant=reg,
                notification_type='ROUND2_SELECTED',
                message="You have been shortlisted for Round 2. Please log in to your dashboard and form your team."
            )
            selected_count += 1
        else:
            RoundNotification.objects.create(
                participant=reg,
                notification_type='ROUND2_NOT_SELECTED',
                message="You were not shortlisted for Round 2. However, you may still participate by joining a team formed by shortlisted participants."
            )
            not_selected_count += 1
            
    modeladmin.message_user(request, f"📢 Pushed Round 2 notifications: {selected_count} shortlisted, {not_selected_count} non-shortlisted.")

push_round2_selection.short_description = "📢 Push Round 2 Selection Notification"

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
    
    actions = [export_as_csv, mark_round2_qualified, mark_round3_qualified, verify_payments_bulk, mark_attendance_present_bulk, push_round2_selection]
    
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

@admin.register(RoundTimingSettings)
class RoundTimingSettingsAdmin(ModelAdmin):
    list_display = ('__str__', 'team_formation_status_tag', 'ppt_submission_status_tag', 'team_formation_start', 'team_formation_end', 'ppt_submission_start', 'ppt_submission_end')
    
    def has_add_permission(self, request):
        return not RoundTimingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def team_formation_status_tag(self, obj):
        from django.utils.html import format_html
        status = obj.get_team_formation_status()
        colors = {'LOCKED': '#ef4444', 'OPEN': '#22c55e', 'CLOSED': '#64748b'}
        return format_html('<b style="color: {};">{}</b>', colors.get(status, 'black'), status)
    team_formation_status_tag.short_description = "Formation Status"

    def ppt_submission_status_tag(self, obj):
        from django.utils.html import format_html
        status = obj.get_ppt_submission_status()
        colors = {'LOCKED': '#ef4444', 'OPEN': '#22c55e', 'CLOSED': '#64748b'}
        return format_html('<b style="color: {};">{}</b>', colors.get(status, 'black'), status)
    ppt_submission_status_tag.short_description = "Submission Status"

@admin.register(FreeEntryWhitelist)
class FreeEntryWhitelistAdmin(ModelAdmin):
    list_display = ('value', 'whitelist_type', 'description')
    list_filter = ('whitelist_type',)
    search_fields = ('value', 'description')



class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 0
    readonly_fields = ('participant_email',)
    
    def participant_email(self, obj):
        return obj.participant.email
    participant_email.short_description = "Email"

def export_teams_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=teams_export.csv'
    writer = csv.writer(response)
    
    writer.writerow(['Team ID', 'Team Name', 'Creator Name', 'Creator Email', 'Status', 'Selected for Round 3', 'Members', 'Created At'])
    
    for team in queryset:
        members = ", ".join([f"{m.participant.name} ({m.participant.email})" for m in team.members.all()])
        writer.writerow([
            team.team_id,
            team.team_name,
            team.creator.name,
            team.creator.email,
            team.status,
            'YES' if team.selected_for_round3 else 'NO',
            members,
            team.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    return response
export_teams_as_csv.short_description = "🚀 Export Selected Teams to CSV"

@admin.register(Team)
class TeamAdmin(ModelAdmin):
    list_display = ('team_id', 'team_name', 'creator_name', 'status_tag', 'member_count', 'selected_for_round3', 'created_at')
    list_filter = ('status', 'selected_for_round3', 'created_at')
    search_fields = ('team_id', 'team_name', 'creator__name', 'creator__email', 'members__participant__name', 'members__participant__email')
    inlines = [TeamMemberInline]
    actions = [export_teams_as_csv, 'push_to_round3']
    
    def creator_name(self, obj):
        return obj.creator.name
    creator_name.short_description = "Team Leader"
    
    def member_count(self, obj):
        return obj.members.count() + 1
    member_count.short_description = "Unit Size"

    def status_tag(self, obj):
        from django.utils.html import format_html
        colors = {
            'DRAFT': 'background: #3b82f620; color: #3b82f6; border: 1px solid #3b82f640;',
            'CONFIRMED': 'background: #22d3ee20; color: #22d3ee; border: 1px solid #22d3ee40; font-weight: bold;'
        }
        return format_html(
            '<span style="padding: 4px 10px; border-radius: 20px; font-size: 10px; text-transform: uppercase; {}">{} {}</span>',
            colors.get(obj.status, ''),
            obj.status,
            '🔒' if obj.status == 'CONFIRMED' else '📝'
        )
    status_tag.short_description = "Security Status"

    def push_to_round3(self, request, queryset):
        queryset.update(selected_for_round3=True)
        # Notify all members
        from .models import RoundNotification
        for team in queryset:
            for member_rel in team.members.all():
                RoundNotification.objects.create(
                    participant=member_rel.participant,
                    notification_type='ROUND3_SELECTED',
                    message=f"Congratulations! Your team {team.team_id} ({team.team_name}) has been shortlisted for Round 3."
                )
            RoundNotification.objects.create(
                participant=team.creator,
                notification_type='ROUND3_SELECTED',
                message=f"Congratulations! Your team {team.team_id} ({team.team_name}) has been shortlisted for Round 3."
            )
        self.message_user(request, f"⭐ {queryset.count()} teams shortlisted for Round 3.")
    push_to_round3.short_description = "⭐ Shortlist Teams for Round 3"

@admin.register(Round3Submission)
class Round3SubmissionAdmin(ModelAdmin):
    list_display = ('team_id_display', 'team_name_display', 'uploaded_by', 'ppt_download_link', 'uploaded_at')
    search_fields = ('team__team_id', 'team__team_name', 'uploaded_by__name')

    def team_id_display(self, obj):
        return obj.team.team_id
    team_id_display.short_description = "Team ID"

    def team_name_display(self, obj):
        return obj.team.team_name
    team_name_display.short_description = "Team Name"

    def ppt_download_link(self, obj):
        from django.utils.html import format_html
        if obj.ppt_file:
            return format_html('<a href="{}" target="_blank" style="color: #8b5cf6; font-weight: bold;">📥 Download PPT</a>', obj.ppt_file.url)
        return "No File"
    ppt_download_link.short_description = "Presentation"

from .admin_attendance import * # Load attendance from separate file

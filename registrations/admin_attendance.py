from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import AttendanceSession, AttendanceRecord
from .views import generate_attendance_qr
from unfold.admin import ModelAdmin

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'get_qr_preview')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('session_id', 'get_qr_preview', 'get_total_participants', 'get_present_count', 'get_absent_count')

    def get_qr_preview(self, obj):
        if obj.session_id:
            # We need a request object for absolute URL, but let's just show a simple link 
            # or try to provide a preview if we are in admin. 
            # In a real scenario, we'd use a custom admin view for this.
            return mark_safe(f'<a href="/attendance/checkin/{obj.session_id}/" target="_blank" style="color:#06b6d4; font-weight:bold;">View Target URL</a>')
        return "-"
    get_qr_preview.short_description = "Attendance URL"

    def get_total_participants(self, obj):
        from .models import UserRegistration
        return UserRegistration.objects.filter(registration_type='PARTICIPANT').count()
    get_total_participants.short_description = "Total Participants"

    def get_present_count(self, obj):
        return obj.records.filter(status='PRESENT').count()
    get_present_count.short_description = "Present"

    def get_absent_count(self, obj):
        total = self.get_total_participants(obj)
        present = self.get_present_count(obj)
        return total - present
    get_absent_count.short_description = "Absent"

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(ModelAdmin):
    list_display = ('participant', 'session', 'status', 'timestamp')
    list_filter = ('session', 'status', 'timestamp')
    search_fields = ('participant__name', 'participant__email', 'session__name')

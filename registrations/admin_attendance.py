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
            from .views import generate_attendance_qr
            # Since we don't have request here easily for list_display, 
            # we'll use a placeholder/relative URL or try to get current site
            # For the admin list view, we'll try to use a simple relative URL QR
            import qrcode
            import base64
            from io import BytesIO
            
            # Use a dummy request-like object or just build the URL
            # In a production environment, you'd want the full domain.
            url = f"/attendance/checkin/{obj.session_id}/"
            
            qr = qrcode.QRCode(version=1, box_size=5, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return mark_safe(f'<div style="text-align:center;"><img src="data:image/png;base64,{qr_base64}" /><br/><code style="font-size:10px;">{url}</code></div>')
        return "-"
    get_qr_preview.short_description = "Attendance QR"

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

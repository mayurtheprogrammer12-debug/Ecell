import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from .models import AttendanceSession, AttendanceRecord
from unfold.admin import ModelAdmin

def export_attendance_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=attendance_records.csv'
    writer = csv.writer(response)

    writer.writerow(['Participant Name', 'Email', 'College', 'Session', 'Status', 'Timestamp'])

    for obj in queryset:
        writer.writerow([
            obj.participant.name,
            obj.participant.email,
            obj.participant.college,
            obj.session.name,
            obj.status,
            obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response

export_attendance_as_csv.short_description = "🚀 Export Selected to CSV (Excel)"

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'get_qr_preview', 'total_count', 'present_count', 'absent_count')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('session_id', 'get_qr_preview', 'total_count', 'present_count', 'absent_count')

    def get_qr_preview(self, obj):
        if obj.session_id:
            import qrcode
            import base64
            from io import BytesIO
            
            domain = "ennovatex.up.railway.app"
            url = f"https://{domain}/attendance/checkin/{obj.session_id}/"
            
            qr = qrcode.QRCode(version=1, box_size=5, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return mark_safe(f'''
                <div style="text-align:center;">
                    <img id="qr-{obj.id}" src="data:image/png;base64,{qr_base64}" /><br/>
                    <div style="margin-top:10px; display:flex; gap:5px; justify-content:center;">
                        <a href="/attendance/session/{obj.session_id}/qr/" target="_blank" 
                           style="padding:6px 12px; background:#06b6d4; color:white; border-radius:8px; font-size:11px; text-decoration:none; font-weight:800; text-transform:uppercase; letter-spacing:0.05em;">
                           Full Screen
                        </a>
                        <a href="data:image/png;base64,{qr_base64}" download="attendance_qr_{obj.id}.png"
                           style="padding:6px 12px; background:#4c1d95; color:white; border-radius:8px; font-size:11px; text-decoration:none; font-weight:800; text-transform:uppercase; letter-spacing:0.05em;">
                           Download
                        </a>
                    </div>
                </div>
            ''')
        return "-"
    get_qr_preview.short_description = "Attendance QR"

    def total_count(self, obj):
        from .models import UserRegistration
        return UserRegistration.objects.filter(registration_type='PARTICIPANT').count()
    total_count.short_description = "Total registered"

    def present_count(self, obj):
        return obj.records.filter(status='PRESENT').count()
    present_count.short_description = "Marked Present"

    def absent_count(self, obj):
        total = self.total_count(obj)
        present = self.present_count(obj)
        return total - present
    absent_count.short_description = "Marked Absent"

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(ModelAdmin):
    list_display = (
        'participant_name', 'participant_email', 'session_link', 
        'status', 'timestamp'
    )
    list_filter = ('session', 'status', 'timestamp')
    search_fields = ('participant__name', 'participant__email', 'session__name')
    actions = [export_attendance_as_csv]

    def participant_name(self, obj):
        return obj.participant.name
    participant_name.short_description = "Participant Name"

    def participant_email(self, obj):
        return obj.participant.email
    participant_email.short_description = "Email"

    def session_link(self, obj):
        return obj.session.name
    session_link.short_description = "Session"

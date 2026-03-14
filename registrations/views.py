import json
import uuid
import qrcode
import base64
import urllib.parse
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import UserRegistration, AttendanceSession, AttendanceRecord
from .forms import ParticipantForm, ExhibitorForm, Round1SubmissionForm
from payments.models import PaymentRecord
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from .signals import send_email_in_background

@login_required(login_url='login')
def round1_submit(request):
    registration = get_object_or_404(UserRegistration, user=request.user)
    
    if registration.round1_completed:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = Round1SubmissionForm(request.POST, instance=registration)
        if form.is_valid():
            reg = form.save(commit=False)
            reg.round1_completed = True
            reg.round1_submitted_at = timezone.now()
            reg.save()
            return redirect('dashboard')
    else:
        form = Round1SubmissionForm(instance=registration)
        
    return render(request, 'registrations/round1_form.html', {
        'form': form,
        'registration': registration
    })

@login_required(login_url='login')
def round2_view(request):
    registration = getattr(request.user, 'registration', None)
    if not registration or not registration.selected_for_round2:
        return redirect('dashboard')
    
    team = Team.objects.filter(creator=registration).first()
    context = {
        'registration': registration,
        'team': team,
    }
    return render(request, 'registrations/round2.html', context)

def generate_upi_qr(upi_id, payee_name, amount, transaction_note):
    # Simplest possible UPI link
    # pa: Payee address
    # pn: Payee name (Simple, no spaces/special chars)
    # am: Amount (2 decimal places)
    # cu: Currency
    # tn: Note
    
    payee_name_simple = "PCCOE" 
    amount_formatted = "{:.2f}".format(float(amount))
    transaction_note_encoded = urllib.parse.quote(transaction_note)
    
    # We remove mc, mode, and tr to make it a 'simple' personal payment link
    # which avoids triggering 'Business Intent' security checks in some apps
    upi_url = f"upi://pay?pa={upi_id}&pn={payee_name_simple}&am={amount_formatted}&cu=INR&tn={transaction_note_encoded}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return qr_base64, upi_url

def create_auth_user(email, password, registration):
    # Check if a user with this email/username already exists
    user = User.objects.filter(username=email).first()
    
    if not user:
        # Create new user if they don't exist
        user = User.objects.create_user(username=email, email=email, password=password)
    else:
        # If user exists, update their password to the newly provided one
        user.set_password(password)
        user.save()
        
    registration.user = user
    registration.save()
    return user

from .models import Team, TeamMember
from django.db.models import Q

@login_required(login_url='login')
def search_team_members(request):
    registration = getattr(request.user, 'registration', None)
    if not registration or not registration.selected_for_round2:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    query = request.GET.get('q', '')
    if len(query) < 3:
        return JsonResponse({'results': []})

    # Rule: Not shortlisted for Round 2 AND not already in any team
    eligible_participants = UserRegistration.objects.filter(
        registration_type='PARTICIPANT',
        selected_for_round2=False,
        team_membership__isnull=True
    ).filter(
        Q(name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query)
    )[:10]

    results = []
    for p in eligible_participants:
        results.append({
            'id': p.id,
            'name': p.name,
            'email': p.email,
            'college': p.college
        })

    return JsonResponse({'results': results})

@login_required(login_url='login')
def manage_team(request):
    registration = getattr(request.user, 'registration', None)
    if not registration or not registration.selected_for_round2:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    from .models import RoundTimingSettings
    if RoundTimingSettings.get_settings().get_team_formation_status() != 'OPEN':
        return JsonResponse({'status': 'error', 'message': 'Team formation window is closed'}, status=403)

    if request.method == 'POST':
        team_name = request.POST.get('team_name')
        if not team_name:
            return JsonResponse({'error': 'Team name is required'}, status=400)

        team, created = Team.objects.get_or_create(
            creator=registration,
            defaults={'team_name': team_name}
        )
        if not created and team.status == 'CONFIRMED':
            return JsonResponse({'error': 'Confirmed teams cannot be edited'}, status=400)
        
        team.team_name = team_name
        team.save()
        return JsonResponse({'success': True, 'team_id': team.id})

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required(login_url='login')
def add_team_member(request):
    registration = getattr(request.user, 'registration', None)
    if not registration or not registration.selected_for_round2:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    from .models import RoundTimingSettings
    if RoundTimingSettings.get_settings().get_team_formation_status() != 'OPEN':
        return JsonResponse({'status': 'error', 'message': 'Team formation window is closed'}, status=403)

    team = get_object_or_404(Team, creator=registration)
    if team.status == 'CONFIRMED':
        return JsonResponse({'error': 'Confirmed teams cannot be edited'}, status=400)

    if team.members.count() >= 5: # 5 members + 1 creator = 6 total
        return JsonResponse({'error': 'Maximum team size of 6 reached (including you)'}, status=400)

    participant_id = request.POST.get('participant_id')
    participant = get_object_or_404(UserRegistration, id=participant_id)

    if participant.selected_for_round2:
        return JsonResponse({'error': 'Only non-shortlisted participants can be added to teams'}, status=400)

    if TeamMember.objects.filter(participant=participant).exists():
        return JsonResponse({'error': 'Participant is already in a team'}, status=400)

    TeamMember.objects.create(team=team, participant=participant)
    return JsonResponse({'success': True})

@login_required(login_url='login')
def remove_team_member(request):
    registration = getattr(request.user, 'registration', None)
    if not registration or not registration.selected_for_round2:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    from .models import RoundTimingSettings
    if RoundTimingSettings.get_settings().get_team_formation_status() != 'OPEN':
        return JsonResponse({'status': 'error', 'message': 'Team formation window is closed'}, status=403)

    team = get_object_or_404(Team, creator=registration)
    if team.status == 'CONFIRMED':
        return JsonResponse({'error': 'Confirmed teams cannot be edited'}, status=400)

    participant_id = request.POST.get('participant_id')
    TeamMember.objects.filter(team=team, participant_id=participant_id).delete()
    return JsonResponse({'success': True})

@login_required(login_url='login')
def confirm_team(request):
    registration = getattr(request.user, 'registration', None)
    if not registration or not registration.selected_for_round2:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    from .models import RoundTimingSettings
    if RoundTimingSettings.get_settings().get_team_formation_status() != 'OPEN':
        return JsonResponse({'status': 'error', 'message': 'Team formation window is closed'}, status=403)

    team = get_object_or_404(Team, creator=registration)
    if team.status == 'CONFIRMED':
        return JsonResponse({'error': 'Team is already confirmed'}, status=400)

    team.status = 'CONFIRMED'
    team.save()
    return JsonResponse({'success': True})

def landing_page(request):
    return render(request, 'registrations/landing.html')

def register_choice(request):
    return render(request, 'registrations/choice.html')

def register_participant(request):
    role = request.GET.get('role', 'student').upper()
    if role not in ['STUDENT', 'VISITOR', 'PARTICIPANT']:
        role = 'PARTICIPANT'
        
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            # Map role to registration type
            if role == 'VISITOR':
                registration.registration_type = 'VISITOR'
            else:
                registration.registration_type = 'PARTICIPANT'
            
            # Logic for fee
            base_price = settings.BASE_PARTICIPANT_FEE
            if role == 'VISITOR':
                # Maybe visitors have a different fee? For now assume same as participant
                # but we could adjust here.
                pass
            
            registration.base_price = base_price

            if registration.is_free_eligible:
                registration.discount_amount = base_price
                registration.final_price = 0
                registration.payment_status = 'FREE'
                registration.reference_id = f"FREE-{uuid.uuid4().hex[:8].upper()}"
                registration.save()
                
                # Create User Account
                create_auth_user(registration.email, form.cleaned_data['password'], registration)
                
                # Send Confirmation Email for FREE registration
                try:
                    dashboard_url = "https://ennovatex26.in/dashboard/"
                    subject = "Registration Successful – PCCOE Entrepreneurship Event"
                    context = {
                        'participant_name': registration.name,
                        'dashboard_url': dashboard_url,
                        'logo_url': "https://ennovatex26.in/static/images/logo.png"
                    }
                    html_message = render_to_string('emails/registration_success.html', context)
                    plain_message = strip_tags(html_message)
                    send_email_in_background(
                        subject, plain_message, 'EnnovateX <prince@ennovatex26.in>', registration.email, html_message, registration.pk, 'registration'
                    )
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Failed to send free registration email: {str(e)}")

                return redirect('registration_success', reg_id=registration.id)
            else:
                discount_amount = 0
                referral_code_obj = form.cleaned_data.get('referral_code')
                if referral_code_obj:
                    registration.referral_code_used = referral_code_obj
                    discount_percentage = referral_code_obj.discount_percentage
                    discount_amount = (base_price * discount_percentage) / 100
                
                registration.discount_amount = discount_amount
                registration.final_price = base_price - discount_amount
                
                # Apply safe guard
                if registration.final_price <= 0:
                    registration.final_price = 0
                    registration.payment_status = 'FREE'
                    registration.reference_id = f"FREE-{uuid.uuid4().hex[:8].upper()}"
                    registration.save()
                    
                    # Create User Account
                    create_auth_user(registration.email, form.cleaned_data['password'], registration)
                    
                    if referral_code_obj:
                        referral_code_obj.current_usage += 1
                        referral_code_obj.save()
                    return redirect('registration_success', reg_id=registration.id)

                registration.payment_status = 'PENDING'
                registration.reference_id = f"ECELL-REG-{uuid.uuid4().hex[:8].upper()}"
                
                # IMPORTANT: Data is NOT stored in DB yet. 
                # We store it in session until payment_verify is called with a transaction ID.
                pending_data = {
                    'name': registration.name,
                    'gender': registration.gender,
                    'age': registration.age,
                    'phone': registration.phone,
                    'email': registration.email,
                    'city': registration.city,
                    'college': registration.college,
                    'registration_type': registration.registration_type,
                    'base_price': str(registration.base_price),
                    'discount_amount': str(registration.discount_amount),
                    'final_price': str(registration.final_price),
                    'referral_code_id': referral_code_obj.id if referral_code_obj else None,
                    'password': form.cleaned_data['password'], # Store password to create User later
                    'reference_id': registration.reference_id,
                }
                request.session['pending_registration'] = pending_data
                
                # Prepare context for payment page
                upi_id = "princevallecha@upi"
                payee_name = "PCCOE ECell"
                amount = int(registration.final_price)
                
                qr_base64, upi_url = generate_upi_qr(upi_id, payee_name, amount, registration.reference_id)
                
                context = {
                    'registration': registration, # Instance without ID
                    'upi_id': upi_id,
                    'amount': amount,
                    'qr_base64': qr_base64,
                    'upi_url': upi_url,
                    'reference_id': registration.reference_id,
                    'role': role
                }
                return render(request, 'registrations/payment.html', context)
    else:
        form = ParticipantForm()
    
    return render(request, 'registrations/participant_form.html', {'form': form, 'role': role})

def register_exhibitor(request):
    if request.method == 'POST':
        form = ExhibitorForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.registration_type = 'EXHIBITOR'
            registration.payment_status = 'FREE'
            registration.final_price = 0
            registration.reference_id = f"FREE-{uuid.uuid4().hex[:8].upper()}"
            registration.save()
            
            # Create User Account
            create_auth_user(registration.email, form.cleaned_data['password'], registration)
            
            # Send Confirmation Email for FREE EXHIBITOR
            try:
                dashboard_url = "https://ennovatex26.in/dashboard/"
                subject = "Registration Successful – PCCOE Entrepreneurship Event"
                context = {
                    'participant_name': registration.name,
                    'dashboard_url': dashboard_url,
                    'logo_url': "https://ennovatex26.in/static/images/logo.png"
                }
                html_message = render_to_string('emails/registration_success.html', context)
                plain_message = strip_tags(html_message)
                send_email_in_background(
                    subject, plain_message, 'EnnovateX <prince@ennovatex26.in>', registration.email, html_message, registration.pk, 'registration'
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to send exhibitor registration email: {str(e)}")

            return redirect('registration_success', reg_id=registration.id)
    else:
        form = ExhibitorForm()
    return render(request, 'registrations/exhibitor_form.html', {'form': form})

def payment_verify(request):
    if request.method == 'POST':
        screenshot = request.FILES.get('screenshot')
        
        # Retrieve data from session
        pending_data = request.session.get('pending_registration')
        if not pending_data:
            # Fallback for older sessions or issues - check if user already exists
            # but ideally we want to force re-registration if no data exists.
            return render(request, 'registrations/participant_form.html', {
                'error': 'Session expired. Please register again before payment.',
                'role': 'PARTICIPANT'
            })

        # Check if email already registered (to avoid duplicates)
        if UserRegistration.objects.filter(email=pending_data['email']).exists():
             registration = UserRegistration.objects.get(email=pending_data['email'])
        else:
            # Create the actual registration record now!
            registration = UserRegistration(
                name=pending_data['name'],
                gender=pending_data['gender'],
                age=pending_data['age'],
                phone=pending_data['phone'],
                email=pending_data['email'],
                city=pending_data['city'],
                college=pending_data['college'],
                registration_type=pending_data['registration_type'],
                base_price=pending_data['base_price'],
                discount_amount=pending_data['discount_amount'],
                final_price=pending_data['final_price'],
                reference_id=pending_data['reference_id'],
                payment_status='PENDING'
            )
            if pending_data.get('referral_code_id'):
                registration.referral_code_used_id = pending_data['referral_code_id']
            registration.save()
            
            # Create User Account
            create_auth_user(registration.email, pending_data['password'], registration)

            # Update Referral Usage
            if registration.referral_code_used:
                registration.referral_code_used.current_usage += 1
                registration.referral_code_used.save()

        # Create Payment Record
        record = PaymentRecord.objects.create(
            registration=registration,
            reference_id=registration.reference_id,
            amount=registration.final_price,
            payment_status='pending'
        )
        if screenshot:
            record.screenshot = screenshot
            record.save()
            
        registration.payment_status = 'PENDING'
        registration.save()

        # Clear session
        if 'pending_registration' in request.session:
            del request.session['pending_registration']

        # Send Confirmation Email AFTER payment success redirect
        if not registration.registration_email_sent:
            try:
                dashboard_url = "https://ennovatex26.in/dashboard/"
                subject = "Registration Successful – PCCOE Entrepreneurship Event"
                context = {
                    'participant_name': registration.name,
                    'dashboard_url': dashboard_url,
                    'logo_url': "https://ennovatex26.in/static/images/logo.png"
                }
                html_message = render_to_string('emails/registration_success.html', context)
                plain_message = strip_tags(html_message)
                send_email_in_background(
                    subject, plain_message, 'EnnovateX <prince@ennovatex26.in>', registration.email, html_message, registration.pk, 'registration'
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to send payment-success registration email: {str(e)}")
            
        return redirect('registration_success', reg_id=registration.id)

    return HttpResponseBadRequest('Invalid request')

def registration_success(request, reg_id):
    registration = get_object_or_404(UserRegistration, id=reg_id)
    return render(request, 'registrations/success.html', {'registration': registration})

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            return render(request, 'registrations/login.html', {'error': 'Invalid credentials'})
    return render(request, 'registrations/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def dashboard(request):
    registration = getattr(request.user, 'registration', None)
    if not registration:
        return redirect('register_choice')
    
    # Notifications Logic
    from .models import RoundNotification, Round3Submission
    notifications = RoundNotification.objects.filter(participant=registration).order_by('-created_at')
    
    # Team Visibility Logic
    team = None
    if registration.selected_for_round2:
        team = Team.objects.filter(creator=registration).first()
    
    if not team:
        membership = TeamMember.objects.filter(participant=registration, team__status='CONFIRMED').first()
        if membership:
            team = membership.team
            
    # Round 3 Submission Status
    ppt_submitted = False
    if team and team.selected_for_round3:
        ppt_submitted = Round3Submission.objects.filter(team=team).exists()
    
    # Timing Logic
    from .models import RoundTimingSettings
    timing = RoundTimingSettings.get_settings()
    
    context = {
        'registration': registration,
        'team': team,
        'notifications': notifications,
        'ppt_submitted': ppt_submitted,
        'timing': timing,
        'formation_status': timing.get_team_formation_status(),
        'ppt_status': timing.get_ppt_submission_status(),
    }
    return render(request, 'registrations/dashboard.html', context)

@login_required(login_url='login')
def attendance_checkin(request, session_id):
    session = get_object_or_404(AttendanceSession, session_id=session_id)
    registration = getattr(request.user, 'registration', None)
    
    context = {
        'session': session,
        'registration': registration,
    }

    if not registration:
        # If user is staff/admin but no registration, show error
        if request.user.is_staff:
            context['error'] = "Admins must have a Participant record to mark attendance. Please register as a participant first."
            return render(request, 'registrations/attendance_page.html', context)
        return redirect('register_choice')

    if registration.registration_type != 'PARTICIPANT':
        context['error'] = f"Attendance is only for Participants. Your registration type is {registration.get_registration_type_display()}."
        return render(request, 'registrations/attendance_page.html', context)

    # Check if attendance already exists
    attendance = AttendanceRecord.objects.filter(participant=registration, session=session).first()
    context['attendance'] = attendance
    
    if request.method == 'POST':
        if not session.is_active:
            context['error'] = "This attendance session is no longer active."
            return render(request, 'registrations/attendance_page.html', context)
            
        if attendance:
             context['info'] = "Attendance already recorded."
             return render(request, 'registrations/attendance_page.html', context)
        
        AttendanceRecord.objects.create(
            participant=registration,
            session=session,
            status='PRESENT'
        )
        context['success'] = True
        context['attendance'] = True # Set to true to hide the button

    return render(request, 'registrations/attendance_page.html', context)

def generate_attendance_qr(session_id, request):
    # Absolute URL for the QR code
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    url = f"{protocol}://{domain}/attendance/checkin/{session_id}/"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return qr_base64, url

@login_required(login_url='login')
def show_session_qr(request, session_id):
    # This view is for organizers to show the QR code on a screen
    if not request.user.is_staff:
        return redirect('dashboard')
        
    session = get_object_or_404(AttendanceSession, session_id=session_id)
    qr_base64, full_url = generate_attendance_qr(session_id, request)
    
    return render(request, 'registrations/show_qr.html', {
        'session': session,
        'qr_base64': qr_base64,
        'full_url': full_url
    })

@login_required(login_url='login')
def upload_round3_ppt(request):
    registration = getattr(request.user, 'registration', None)
    if not registration:
        return JsonResponse({'status': 'error', 'message': 'Registration not found'}, status=404)
        
    from .models import RoundTimingSettings
    if RoundTimingSettings.get_settings().get_ppt_submission_status() != 'OPEN':
        return JsonResponse({'status': 'error', 'message': 'PPT submission window is closed'}, status=403)
    team = registration.get_team()
    if not team or not team.selected_for_round3:
        return JsonResponse({'status': 'error', 'message': 'Team not shortlisted for Round 3'}, status=403)
        
    if team.status != 'CONFIRMED':
        return JsonResponse({'status': 'error', 'message': 'Team must be confirmed before submission'}, status=403)

    if request.method == 'POST' and request.FILES.get('ppt_file'):
        from .models import Round3Submission
        ppt_file = request.FILES['ppt_file']
        
        # Validate extension
        ext = ppt_file.name.split('.')[-1].lower()
        if ext not in ['ppt', 'pptx']:
            return JsonResponse({'status': 'error', 'message': 'Only PPT/PPTX files allowed'}, status=400)
            
        submission, created = Round3Submission.objects.update_or_create(
            team=team,
            defaults={'uploaded_by': registration, 'ppt_file': ppt_file}
        )
        
        return JsonResponse({'status': 'success', 'message': 'PPT submitted successfully'})
        
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

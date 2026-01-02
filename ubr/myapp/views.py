from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignUpForm
from .models import Profile, InspectionRequest, InspectionReport, Message  # import your models
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .decorators import role_required
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache



def signup(request):
    """
    Handle user registration with user_type selection.
    After signup, redirect to the proper dashboard.
    """
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            # If the user selected `Admin` during signup, grant Django admin privileges.
            # WARNING: this makes any signup selecting Admin a true superuser.
            if form.cleaned_data.get('user_type') == 'Admin':
                user.is_staff = True
                user.is_superuser = True
                user.save()
            # Create or update Profile with selected user_type
            Profile.objects.update_or_create(
                user=user,
                defaults={'user_type': form.cleaned_data['user_type']}
            )
            login(request, user)
            messages.success(
                request,
                f'Account created successfully! Welcome, {user.username}!'
            )
            return redirect('dashboard_redirect')
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form})


def home(request):
    """
    Simple home page view.
    """
    return render(request, 'home.html')


@login_required
def dashboard_redirect(request):
    """
    Redirect users to the correct dashboard based on user_type.
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if profile.user_type == 'Owner':
        return redirect('owner_dashboard')
    elif profile.user_type == 'Inspector':
        return redirect('inspector_dashboard')
    elif profile.user_type == 'Admin':
        return redirect('admin_dashboard')
    else:
        return redirect('home')


@login_required
@role_required('Owner')
def owner_dashboard(request):
    """
    Show inspection requests for the logged-in building owner.
    """
    requests = list(InspectionRequest.objects.filter(owner=request.user))
    # attach report object if exists to avoid template OneToOne access errors
    from .models import InspectionReport
    for req in requests:
        try:
            req.report_obj = req.report
        except InspectionReport.DoesNotExist:
            req.report_obj = None
    return render(request, 'owner/dashboard.html', {'data': requests})


@login_required
@role_required('Inspector')
def inspector_dashboard(request):
    """
    Show inspection requests assigned to the logged-in inspector.
    """
    requests = InspectionRequest.objects.filter(inspector=request.user)
    return render(request, 'inspector/dashboard.html', {'data': requests})


@login_required
def edit_profile(request):
    """Allow users (inspectors) to edit their profile fields."""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    from .forms import ProfileForm
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            # Redirect back to the appropriate dashboard
            if profile.user_type == 'Inspector':
                return redirect('inspector_dashboard')
            return redirect('dashboard_redirect')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'inspector/edit_profile.html', {'form': form, 'profile': profile})


@login_required
@role_required('Admin')
def admin_dashboard(request):
    """
    Show all inspection requests to admin with optional balance info.
    """
    # Only allow Admin users (staff check remains as an extra safety net)
    # role_required is not applied here because some admin-only flows check is_staff
    requests = InspectionRequest.objects.all()
    # get or create single AdminBalance row
    from .models import AdminBalance, Profile
    admin_balance_obj, _ = AdminBalance.objects.get_or_create(pk=1)
    # pending inspector approvals
    pending_inspectors = Profile.objects.filter(user_type='Inspector', is_approved=False)
    return render(request, 'admin/dashboard.html', {'data': requests, 'admin_balance': admin_balance_obj, 'pending_inspectors': pending_inspectors})


# views.py
from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    logout(request)
    return redirect('home')


@login_required
def request_inspection(request):
    """Owner: request an inspection (simple handler)."""
    if request.method == 'POST':
        location = request.POST.get('location') or request.POST.get('building_location')
        # Create InspectionRequest with minimal required fields
        InspectionRequest.objects.create(owner=request.user, building_location=location)
        messages.success(request, 'Inspection request submitted.')
        return redirect('owner_dashboard')
    return render(request, 'owner/request_inspection.html')


@login_required
def owner_complaint(request):
    """Submit a complaint to an inspector. Template expects `inspectors` context."""
    inspectors = User.objects.filter(profile__user_type='Inspector')
    if request.method == 'POST':
        inspector_id = request.POST.get('inspector')
        message_text = request.POST.get('message', '').strip()
        inspector = None
        if inspector_id:
            try:
                inspector = User.objects.get(pk=inspector_id)
            except User.DoesNotExist:
                inspector = None
        # Create complaint record
        from .models import Complaint
        Complaint.objects.create(reporter=request.user, against_inspector=inspector, message=message_text)
        messages.success(request, 'Complaint submitted to the inspector.')
        return redirect('owner_dashboard')
    return render(request, 'owner/complaints.html', {'inspectors': inspectors})


@login_required
def inbox(request):
    """Show messages received by the current user."""
    received = Message.objects.filter(recipient=request.user).order_by('-sent_at')
    return render(request, 'messages/inbox.html', {'messages': received})


@login_required
def payment(request, pk):
    """Handle a simple payment flow for an InspectionRequest."""
    req = get_object_or_404(InspectionRequest, pk=pk)
    # prefer request-specific fee if set
    amount = req.fee if getattr(req, 'fee', None) else 500
    success = False
    if request.method == 'POST':
        # get chosen method (demo only)
        method = request.POST.get('method', 'Demo')
        # simulate payment success: create Payment and update admin balance
        success = True
        from .models import Payment, AdminBalance
        Payment.objects.create(payer=request.user, inspection_request=req, amount=amount)
        # mark request as Paid
        req.status = 'Paid'
        req.save()
        admin_balance_obj, _ = AdminBalance.objects.get_or_create(pk=1)
        admin_balance_obj.balance = (admin_balance_obj.balance or 0) + amount
        admin_balance_obj.save()
    return render(request, 'owner/payment.html', {'amount': amount, 'success': success})


@login_required
def owner_payments(request):
    """List owner's inspection requests to pick one for payment."""
    requests = InspectionRequest.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'owner/payments_list.html', {'requests': requests})


@login_required
def admin_approve_inspectors(request):
    from .models import Profile
    if request.method == 'POST':
        uid = request.POST.get('profile_id')
        action = request.POST.get('action')
        profile = Profile.objects.get(pk=uid)
        if action == 'approve':
            profile.is_approved = True
            profile.save()
            messages.success(request, f'Inspector {profile.user.username} approved.')
        elif action == 'reject':
            profile.user.delete()
            messages.success(request, f'Inspector {profile.user.username} rejected and user removed.')
        return redirect('admin_dashboard')
    pending = Profile.objects.filter(user_type='Inspector', is_approved=False)
    return render(request, 'admin/approve_inspectors.html', {'pending': pending})


@login_required
def admin_assign_inspector(request, pk=None):
    from .models import Profile
    req = None
    if pk:
        req = get_object_or_404(InspectionRequest, pk=pk)
    inspectors = User.objects.filter(profile__user_type='Inspector', profile__is_approved=True, profile__is_banned=False)
    if request.method == 'POST':
        inspector_id = request.POST.get('inspector')
        inspector = User.objects.get(pk=inspector_id)
        req.inspector = inspector
        req.status = 'Assigned'
        req.save()
        messages.success(request, 'Inspector assigned.')
        return redirect('admin_dashboard')
    return render(request, 'admin/assign_inspector.html', {'inspectors': inspectors, 'request_obj': req})


@login_required
def admin_manage_complaints(request):
    # Restrict to staff/admins
    if not request.user.is_staff:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard_redirect')
    from .models import Complaint, Profile
    if request.method == 'POST':
        cid = request.POST.get('complaint_id')
        action = request.POST.get('action')
        comp = get_object_or_404(Complaint, pk=cid)
        if action == 'resolve':
            comp.resolved = True
            comp.save()
            messages.success(request, f'Complaint {comp.pk} marked resolved.')
        elif action == 'ban' and comp.against_inspector:
            profile, _ = Profile.objects.get_or_create(user=comp.against_inspector)
            profile.is_banned = True
            profile.save()
            messages.success(request, f'Inspector {comp.against_inspector.username} banned.')
        elif action == 'unban' and comp.against_inspector:
            profile, _ = Profile.objects.get_or_create(user=comp.against_inspector)
            profile.is_banned = False
            profile.save()
            messages.success(request, f'Inspector {comp.against_inspector.username} unbanned.')
        elif action == 'respond':
            resp = request.POST.get('admin_response', '')
            comp.admin_response = resp
            comp.resolved = True
            comp.save()
            messages.success(request, f'Responded to complaint {comp.pk}.')
        return redirect('admin_manage_complaints')

    complaints = Complaint.objects.all().order_by('-created_at')
    return render(request, 'admin/complaints.html', {'complaints': complaints})


@login_required
def admin_set_fee(request, pk):
    # Only staff can set fees
    if not request.user.is_staff:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard_redirect')
    req = get_object_or_404(InspectionRequest, pk=pk)
    if request.method == 'POST':
        fee = request.POST.get('fee')
        try:
            req.fee = float(fee)
            req.save()
            messages.success(request, f'Fee updated for request {req.pk}.')
            return redirect('admin_dashboard')
        except (TypeError, ValueError):
            messages.error(request, 'Invalid fee value.')
    return render(request, 'admin/set_fee.html', {'request_obj': req})


@login_required
def admin_view_users(request):
    if not request.user.is_staff:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard_redirect')
    users = User.objects.all().order_by('username')
    from .models import Profile
    if request.method == 'POST':
        action = request.POST.get('action')
        uid = request.POST.get('user_id')
        user = get_object_or_404(User, pk=uid)
        profile, _ = Profile.objects.get_or_create(user=user)
        if action == 'ban':
            profile.is_banned = True
            profile.save()
            messages.success(request, f'User {user.username} banned.')
        elif action == 'unban':
            profile.is_banned = False
            profile.save()
            messages.success(request, f'User {user.username} unbanned.')
        return redirect('admin_view_users')
    # attach profile and counts
    user_rows = []
    for u in users:
        profile, _ = Profile.objects.get_or_create(user=u)
        inspections_count = InspectionRequest.objects.filter(owner=u).count()
        assigned_count = InspectionRequest.objects.filter(inspector=u).count()
        user_rows.append({'user': u, 'profile': profile, 'inspections_count': inspections_count, 'assigned_count': assigned_count})
    return render(request, 'admin/users.html', {'users': user_rows})


@login_required
def inspector_inspection_view(request, pk):
    # Inspector view for a specific inspection request
    req = get_object_or_404(InspectionRequest, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            # create report
            structural = request.POST.get('structural')
            checklist = request.POST.get('checklist')
            decision = 'Approved'
            report = InspectionReport.objects.create(
                inspection_request=req,
                inspector=request.user,
                structural_evaluation=structural,
                compliance_checklist=checklist,
                decision=decision,
                remarks=request.POST.get('remarks','')
            )
            req.status = 'Approved'
            req.save()
            messages.success(request, 'Inspection approved and report generated.')
            return redirect('view_report', pk=report.pk)
        elif action == 'reject':
            reason = request.POST.get('reason')
            report = InspectionReport.objects.create(inspection_request=req, inspector=request.user, decision='Rejected', remarks=reason)
            req.status = 'Rejected'
            req.save()
            messages.success(request, 'Inspection rejected.')
            return redirect('view_report', pk=report.pk)
    return render(request, 'inspector/inspect_request.html', {'req': req})


@login_required
def send_message(request):
    """Send a new internal message to another user."""
    # Restrict recipients to Admins and Inspectors only
    users = User.objects.filter(profile__user_type__in=['Admin', 'Inspector']).exclude(pk=request.user.pk)
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        subject = request.POST.get('subject', '')
        body = request.POST.get('body', '')
        recipient = get_object_or_404(User, pk=recipient_id)
        Message.objects.create(sender=request.user, recipient=recipient, subject=subject, body=body)
        messages.success(request, 'Message sent.')
        return redirect('inbox')
    return render(request, 'messages/send.html', {'users': users})


@login_required
def view_message(request, pk):
    """View a received message and optionally reply."""
    msg = get_object_or_404(Message, pk=pk)
    # Only allow recipient or sender to view (recipient can reply)
    if request.user != msg.recipient and request.user != msg.sender:
        messages.error(request, 'Permission denied.')
        return redirect('inbox')
    if request.user == msg.recipient and not msg.is_read:
        msg.is_read = True
        msg.save()
    if request.method == 'POST':
        # reply
        reply_body = request.POST.get('body', '')
        Message.objects.create(sender=request.user, recipient=msg.sender, subject=f'Re: {msg.subject}', body=reply_body)
        messages.success(request, 'Reply sent.')
        return redirect('inbox')
    return render(request, 'messages/view.html', {'msg': msg})


@login_required
def view_report(request, pk):
    """Render an inspection report for viewing by owner, inspector, or admin."""
    report = get_object_or_404(InspectionReport, pk=pk)
    # permission: owner, inspector, or staff
    if request.user != report.inspection_request.owner and request.user != report.inspector and not request.user.is_staff:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard_redirect')
    return render(request, 'inspector/report.html', {'report': report})


@login_required
def download_report(request, pk):
    """Provide a simple text download of the inspection report."""
    report = get_object_or_404(InspectionReport, pk=pk)
    if request.user != report.inspection_request.owner and request.user != report.inspector and not request.user.is_staff:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard_redirect')

    lines = []
    lines.append(f"Inspection Report #{report.pk}")
    lines.append(f"Owner: {report.inspection_request.owner.username} ({report.inspection_request.owner.email})")
    lines.append(f"Building location: {report.inspection_request.building_location}")
    lines.append(f"Inspection date: {report.inspection_date}")
    lines.append("")
    lines.append("Structural safety evaluation:")
    lines.append(report.structural_evaluation or '(none)')
    lines.append("")
    lines.append("Compliance checklist:")
    lines.append(report.compliance_checklist or '(none)')
    lines.append("")
    lines.append(f"Decision: {report.decision}")
    lines.append("")
    lines.append("Remarks:")
    lines.append(report.remarks or '(none)')

    content = "\n".join(lines)
    resp = HttpResponse(content, content_type='text/plain; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename=inspection_report_{report.pk}.txt'
    return resp


@never_cache
@login_required(login_url='login')
def admin_dashboard(request):
    return render(request, 'admin/dashboard.html')


@never_cache
@login_required(login_url='login')
def owner_dashboard(request):
    return render(request, 'owner/dashboard.html')

@never_cache
@login_required(login_url='login')
def inspector_dashboard(request):
    return render(request, 'inspector/dashboard.html')

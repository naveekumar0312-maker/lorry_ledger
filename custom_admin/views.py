from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from accounts.models import UserProfile
from django.db import transaction

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or (hasattr(user, 'profile') and user.profile.role == 'ADMIN') or user.username == 'admin')

# Login view
def admin_login_view(request):
    if request.user.is_authenticated and is_admin(request.user):
        return redirect('custom_admin:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, 'custom_admin/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if is_admin(user):
                login(request, user)
                return redirect('custom_admin:dashboard')
            else:
                messages.error(request, "You do not have permission to access the admin panel.")
        else:
            messages.error(request, "Invalid credentials.")

    return render(request, 'custom_admin/login.html')

def admin_logout_view(request):
    logout(request)
    messages.success(request, "Logged out of admin panel successfully.")
    return redirect('custom_admin:login')

@user_passes_test(is_admin, login_url='/admin/')
def admin_dashboard_view(request):
    total_users = User.objects.count()
    return render(request, 'custom_admin/dashboard.html', {'total_users': total_users})

@user_passes_test(is_admin, login_url='/admin/')
def admin_user_list_view(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'custom_admin/user_list.html', {'users': users})

@user_passes_test(is_admin, login_url='/admin/')
def admin_user_create_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        mobile_number = request.POST.get('mobile_number', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Validations
        errors = []
        if not full_name:
            errors.append("Full Name is required.")
        if not email:
            errors.append("Email Address is required.")
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors.append("Enter a valid email address.")

        if not mobile_number or len(mobile_number) < 10:
            errors.append("Enter a valid 10-digit mobile number.")
        if not password:
            errors.append("Password is required.")
        elif len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        # Check existing user
        if email and (User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists()):
            errors.append("An account with this email address already exists.")
            
        if mobile_number and UserProfile.objects.filter(phone_number=mobile_number).exists():
            errors.append("An account with this mobile number already exists.")

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'custom_admin/user_form.html', {'post_data': request.POST})

        # Split full name into first and last name
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        try:
            with transaction.atomic():
                # Create user
                user = User.objects.create_user(
                    username=email, # Use email as username
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Create profile
                UserProfile.objects.create(
                    user=user,
                    role='STAFF',
                    phone_number=mobile_number
                )
            
            messages.success(request, "User created successfully.")
            return redirect('custom_admin:user_list')
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
            return render(request, 'custom_admin/user_form.html', {'post_data': request.POST})

    return render(request, 'custom_admin/user_form.html', {'post_data': {}})

@user_passes_test(is_admin, login_url='/admin/')
def admin_user_detail_view(request, id):
    user = get_object_or_404(User, id=id)
    return render(request, 'custom_admin/user_detail.html', {'user_obj': user})

@user_passes_test(is_admin, login_url='/admin/')
def admin_user_edit_view(request, id):
    user = get_object_or_404(User, id=id)
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        mobile_number = request.POST.get('mobile_number', '').strip()
        password = request.POST.get('password', '')

        errors = []
        if not full_name:
            errors.append("Full Name is required.")
        if not email:
            errors.append("Email Address is required.")
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors.append("Enter a valid email address.")

        if not mobile_number or len(mobile_number) < 10:
            errors.append("Enter a valid 10-digit mobile number.")

        if email != user.email and (User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists()):
            errors.append("An account with this email address already exists.")

        if hasattr(user, 'profile'):
            if mobile_number != user.profile.phone_number and UserProfile.objects.filter(phone_number=mobile_number).exists():
                errors.append("An account with this mobile number already exists.")
        else:
            if mobile_number and UserProfile.objects.filter(phone_number=mobile_number).exists():
                errors.append("An account with this mobile number already exists.")

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'custom_admin/user_form.html', {'user_obj': user, 'edit_mode': True})

        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        user.email = email
        user.username = email
        
        if password:
            if len(password) < 8:
                messages.error(request, "Password must be at least 8 characters long.")
                return render(request, 'custom_admin/user_form.html', {'user_obj': user, 'edit_mode': True})
            user.set_password(password)

        user.save()
        
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.phone_number = mobile_number
        profile.save()

        messages.success(request, "User updated successfully.")
        return redirect('custom_admin:user_list')
        
    return render(request, 'custom_admin/user_form.html', {'user_obj': user, 'edit_mode': True})

@user_passes_test(is_admin, login_url='/admin/')
def admin_user_delete_view(request, id):
    user = get_object_or_404(User, id=id)
    if request.method == 'POST':
        if request.user.id == user.id:
            messages.error(request, "You cannot delete yourself.")
            return redirect('custom_admin:user_list')
        
        user.delete()
        messages.success(request, "User deleted successfully.")
        return redirect('custom_admin:user_list')
    
    return render(request, 'custom_admin/user_confirm_delete.html', {'user_obj': user})

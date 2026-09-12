from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.cache import never_cache
from .models import UserProfile

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

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
        if email and User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            errors.append("An account with this email address already exists.")
            
        if mobile_number and UserProfile.objects.filter(phone_number=mobile_number).exists():
            errors.append("An account with this mobile number already exists.")

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'registration/register.html', {'post_data': request.POST})

        # Split full name into first and last name
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # Create user
        user = User.objects.create_user(
            username=email,
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

        messages.success(request, "Registration successful! You can now log in with your credentials.")
        return redirect('accounts:login')

    return render(request, 'registration/register.html', {'post_data': {}})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me')

        if not username_or_email or not password:
            messages.error(request, "Please enter both username/email and password.")
            return render(request, 'registration/login.html')

        # Try authenticating by username / email
        user = authenticate(request, username=username_or_email, password=password)
        if user is None:
            # Try finding user by email
            user_obj = User.objects.filter(email=username_or_email).first()
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)
                
        if user is None:
            # Try finding user by mobile number in UserProfile
            profile = UserProfile.objects.filter(phone_number=username_or_email).first()
            if profile:
                user = authenticate(request, username=profile.user.username, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, "Your account has been deactivated.")
                return render(request, 'registration/login.html')

            login(request, user)

            if not remember_me:
                request.session.set_expiry(0) # Session expires when browser closes
            else:
                request.session.set_expiry(1209600) # 2 weeks

            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            next_url = request.GET.get('next') or 'dashboard:index'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid login credentials. Please try again.")

    return render(request, 'registration/login.html')


@never_cache
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('accounts:login')


@login_required
def profile_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        mobile_number = request.POST.get('mobile_number', '').strip()

        if full_name:
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        if email:
            user.email = email
            user.username = email
        user.save()

        profile.phone_number = mobile_number
        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {'profile': profile})


@login_required
def change_password_view(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user
        if not user.check_password(old_password):
            messages.error(request, "Current password is incorrect.")
            return render(request, 'accounts/change_password.html')

        if len(new_password) < 8:
            messages.error(request, "New password must be at least 8 characters long.")
            return render(request, 'accounts/change_password.html')

        if new_password != confirm_password:
            messages.error(request, "New password confirmation does not match.")
            return render(request, 'accounts/change_password.html')

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)

        messages.success(request, "Password changed successfully.")
        return redirect('accounts:profile')

    return render(request, 'accounts/change_password.html')

import os
import secrets
from urllib.parse import urlencode
import requests
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from repositories import user_repo, doctor_repo, patient_repo
from forms import LoginForm, RegisterPatientForm, RegisterDoctorForm
from utils.image_utils import process_avatar_image

auth_bp = Blueprint('auth', __name__)


def _handle_google_user(userinfo, chosen_role=None):
    """Processes Google user profile info for login or auto-registration."""
    email = (userinfo.get('email') or '').strip().lower()
    name = (userinfo.get('name') or email.split('@')[0].capitalize()).strip()
    picture = userinfo.get('picture')
    google_id = userinfo.get('sub') or userinfo.get('id', '')

    if not email:
        flash('Google account did not provide a valid email address.', 'danger')
        return redirect(url_for('auth.login'))

    role = chosen_role or session.get('oauth_role', 'patient')
    next_url = session.get('oauth_next', '')

    user = user_repo.get_by_email(email)
    if user:
        # Existing user - update picture if empty or default
        if picture and (not user.get('avatar') or 'default_' in user.get('avatar', '')):
            try:
                user_repo.update(user['id'], {'avatar': picture})
                user['avatar'] = picture
            except Exception:
                pass

        csrf_tok = session.get('csrf_token')
        session.clear()
        if csrf_tok:
            session['csrf_token'] = csrf_tok

        session['user_id'] = user['id']
        session['user_role'] = user['role']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['user_avatar'] = user.get('avatar') or picture
        session.permanent = True

        flash(f'Welcome back, {user["name"]}! Signed in with Google.', 'success')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect(url_for('doctor.dashboard' if user['role'] == 'doctor' else 'patient.dashboard'))

    # New user: Create user and linked role profile
    user_avatar = picture or (
        '/static/uploads/default_doctor.png' if role == 'doctor' else '/static/uploads/default_patient.png'
    )
    new_user = user_repo.create({
        'name': name,
        'email': email,
        'phone': '+91 9876543210',
        'city': 'Delhi',
        'role': role,
        'avatar': user_avatar,
        'google_id': google_id,
        'auth_provider': 'google',
        'password_hash': generate_password_hash(secrets.token_urlsafe(24))
    })

    if role == 'doctor':
        doctor_repo.create({
            'user_id': new_user['id'],
            'name': new_user['name'],
            'email': email,
            'phone': new_user['phone'],
            'city': new_user['city'],
            'avatar': user_avatar,
            'specialization': 'General Medicine',
            'doctor_type': 'Hospital',
            'hospital_or_clinic_name': 'City Hospital & Healthcare',
            'qualifications': 'MBBS, MD',
            'experience_years': 5,
            'consultation_fee': 500.0,
            'address': f"City Hospital, {new_user['city']}",
            'working_days': 'Mon - Fri',
            'timings': '09:00 AM - 05:00 PM',
            'about': f"Dr. {new_user['name']} is a verified specialist practitioner providing personalized medical care.",
            'rating': 5.0,
            'review_count': 0
        })
    else:
        patient_repo.create({
            'user_id': new_user['id'],
            'name': new_user['name'],
            'email': email,
            'phone': new_user['phone'],
            'city': new_user['city'],
            'avatar': user_avatar
        })

    csrf_tok = session.get('csrf_token')
    session.clear()
    if csrf_tok:
        session['csrf_token'] = csrf_tok

    session['user_id'] = new_user['id']
    session['user_role'] = new_user['role']
    session['user_name'] = new_user['name']
    session['user_email'] = new_user['email']
    session['user_avatar'] = user_avatar
    session.permanent = True

    flash(f'Welcome to FindMyDOC, {new_user["name"]}! Your {role} account has been created with Google.', 'success')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect(url_for('doctor.dashboard' if role == 'doctor' else 'patient.dashboard'))


@auth_bp.route('/google')
def google_login():
    """Initiates Google OAuth or opens the demo Google Sign-In helper if credentials are not configured."""
    role = request.args.get('role', 'patient')
    next_url = request.args.get('next', '')

    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')

    if client_id and client_secret:
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        session['oauth_role'] = role
        session['oauth_next'] = next_url

        redirect_uri = url_for('auth.google_callback', _external=True)
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
            'prompt': 'select_account'
        }
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return redirect(auth_url)

    # If Google OAuth credentials are not yet set in .env, offer quick demo accounts / simulation
    return render_template('auth/google_demo.html', role=role, next_url=next_url)


@auth_bp.route('/google/callback')
def google_callback():
    """Handles OAuth 2.0 callback from Google servers."""
    error = request.args.get('error')
    if error:
        flash(f'Google sign-in was cancelled: {error}', 'warning')
        return redirect(url_for('auth.login'))

    state = request.args.get('state')
    saved_state = session.get('oauth_state')
    if not state or state != saved_state:
        flash('Authentication state mismatch. Please try signing in again.', 'danger')
        return redirect(url_for('auth.login'))

    code = request.args.get('code')
    if not code:
        flash('No authorization code received from Google.', 'danger')
        return redirect(url_for('auth.login'))

    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
    redirect_uri = url_for('auth.google_callback', _external=True)

    try:
        token_resp = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri
            },
            timeout=10
        )
        if not token_resp.ok:
            flash('Failed to exchange authorization code with Google.', 'danger')
            return redirect(url_for('auth.login'))

        tokens = token_resp.json()
        access_token = tokens.get('access_token')

        userinfo_resp = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        if not userinfo_resp.ok:
            flash('Failed to retrieve user profile from Google.', 'danger')
            return redirect(url_for('auth.login'))

        userinfo = userinfo_resp.json()
        return _handle_google_user(userinfo)
    except Exception as e:
        import traceback
        print(f"[Google Auth Callback Error] {e}\n{traceback.format_exc()}")
        flash(f'Error connecting to Google: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))


@auth_bp.route('/google-simulate', methods=['GET', 'POST'])
def google_simulate():
    """Allows testing Google Sign-In immediately without requiring live Google Cloud credentials."""
    if request.method == 'GET':
        return redirect(url_for('auth.google_login'))

    role = request.form.get('role', 'patient')
    name = (request.form.get('name') or 'Google User').strip()
    email = (request.form.get('email') or 'google.user@gmail.com').strip().lower()
    avatar = request.form.get('avatar', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80')

    userinfo = {
        'sub': f'g-{secrets.token_hex(8)}',
        'name': name,
        'email': email,
        'picture': avatar
    }
    return _handle_google_user(userinfo, chosen_role=role)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        role = session.get('user_role')
        if role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        return redirect(url_for('patient.dashboard'))

    form = LoginForm()
    selected_role = request.args.get('role', 'auto')
    if request.method == 'GET' and selected_role in ['patient', 'doctor']:
        form.role.data = selected_role

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        password = form.password.data
        role_pref = form.role.data

        user = user_repo.get_by_email(email)
        if not user or not check_password_hash(user.get('password_hash', ''), password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/login.html', form=form)

        # Role validation if specific role selected
        if role_pref != 'auto' and user.get('role') != role_pref:
            flash(f'This account is registered as a {user.get("role")}. Please select the appropriate role.', 'warning')
            return render_template('auth/login.html', form=form)

        # Establish session
        csrf_tok = session.get('csrf_token')
        session.clear()
        if csrf_tok:
            session['csrf_token'] = csrf_tok
        session['user_id'] = user['id']
        session['user_role'] = user['role']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session.permanent = True

        flash(f'Welcome back, {user["name"]}!', 'success')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        if user['role'] == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        return redirect(url_for('patient.dashboard'))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        role = session.get('user_role')
        if role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        return redirect(url_for('patient.dashboard'))

    tab = request.args.get('tab', 'patient')
    patient_form = RegisterPatientForm(prefix="pat")
    doctor_form = RegisterDoctorForm(prefix="doc")

    # If patient submission
    if request.method == 'POST' and request.form.get('register_role') == 'patient':
        tab = 'patient'
        if patient_form.validate_on_submit():
            try:
                email = patient_form.email.data.strip().lower()
                if user_repo.get_by_email(email):
                    flash('An account with this email address already exists. Please log in.', 'danger')
                    return render_template('auth/register.html', active_tab=tab, patient_form=patient_form, doctor_form=doctor_form)

                # Process optional uploaded avatar directly in-memory or fallback to default
                uploaded_avatar = process_avatar_image(patient_form.avatar_file.data)
                avatar_url = uploaded_avatar or "/static/uploads/default_patient.png"

                # Create User
                new_user = user_repo.create({
                    "name": patient_form.name.data.strip(),
                    "email": email,
                    "phone": patient_form.phone.data.strip(),
                    "city": patient_form.city.data.strip(),
                    "role": "patient",
                    "avatar": avatar_url,
                    "password_hash": generate_password_hash(patient_form.password.data)
                })

                # Create Patient profile
                patient_repo.create({
                    "user_id": new_user["id"],
                    "name": new_user["name"],
                    "email": new_user["email"],
                    "phone": new_user["phone"],
                    "city": new_user["city"],
                    "avatar": avatar_url
                })

                # Auto login (keep cookie lightweight and well within 4KB browser limit)
                csrf_tok = session.get('csrf_token')
                session.clear()
                if csrf_tok:
                    session['csrf_token'] = csrf_tok
                session['user_id'] = new_user['id']
                session['user_role'] = 'patient'
                session['user_name'] = new_user['name']
                session['user_email'] = new_user['email']
                session.permanent = True

                flash('Welcome to FindMyDOC! Your patient account has been created.', 'success')
                return redirect(url_for('patient.dashboard'))
            except Exception as e:
                import traceback
                print(f"[Patient Registration Error] {e}\n{traceback.format_exc()}")
                flash(f"Database error during registration: {str(e)}. Please check your MongoDB connection and IP whitelist.", 'danger')
                return render_template('auth/register.html', active_tab=tab, patient_form=patient_form, doctor_form=doctor_form)

    # If doctor submission
    elif request.method == 'POST' and request.form.get('register_role') == 'doctor':
        tab = 'doctor'
        if doctor_form.validate_on_submit():
            try:
                email = doctor_form.email.data.strip().lower()
                if user_repo.get_by_email(email):
                    flash('A doctor account with this email address already exists. Please log in.', 'danger')
                    return render_template('auth/register.html', active_tab=tab, patient_form=patient_form, doctor_form=doctor_form)

                # Process optional uploaded avatar directly in-memory or fallback to default
                uploaded_avatar = process_avatar_image(doctor_form.avatar_file.data)
                avatar_url = uploaded_avatar or "/static/uploads/default_doctor.png"

                # Create User
                new_user = user_repo.create({
                    "name": doctor_form.name.data.strip(),
                    "email": email,
                    "phone": doctor_form.phone.data.strip(),
                    "city": doctor_form.city.data.strip(),
                    "role": "doctor",
                    "avatar": avatar_url,
                    "password_hash": generate_password_hash(doctor_form.password.data)
                })

                # Create Doctor Profile
                doctor_repo.create({
                    "user_id": new_user["id"],
                    "name": doctor_form.name.data.strip(),
                    "email": email,
                    "phone": doctor_form.phone.data.strip(),
                    "city": doctor_form.city.data.strip(),
                    "avatar": avatar_url,
                    "specialization": doctor_form.specialization.data,
                    "doctor_type": doctor_form.doctor_type.data,
                    "hospital_or_clinic_name": doctor_form.hospital_or_clinic_name.data.strip(),
                    "qualifications": doctor_form.qualifications.data.strip(),
                    "experience_years": int(doctor_form.experience_years.data or 0),
                    "consultation_fee": float(doctor_form.consultation_fee.data or 150),
                    "address": f"{doctor_form.hospital_or_clinic_name.data.strip()}, {doctor_form.city.data.strip()}",
                    "working_days": "Mon - Fri",
                    "timings": "09:00 AM - 05:00 PM",
                    "about": f"{doctor_form.name.data.strip()} is a specialized {doctor_form.specialization.data} consultant providing exceptional care.",
                    "rating": 5.0,
                    "review_count": 0
                })

                # Auto login (keep cookie lightweight and well within 4KB browser limit)
                csrf_tok = session.get('csrf_token')
                session.clear()
                if csrf_tok:
                    session['csrf_token'] = csrf_tok
                session['user_id'] = new_user['id']
                session['user_role'] = 'doctor'
                session['user_name'] = new_user['name']
                session['user_email'] = new_user['email']
                session.permanent = True

                flash('Welcome Dr. ' + new_user['name'] + '! Your professional doctor profile is ready.', 'success')
                return redirect(url_for('doctor.dashboard'))
            except Exception as e:
                import traceback
                print(f"[Doctor Registration Error] {e}\n{traceback.format_exc()}")
                flash(f"Database error during registration: {str(e)}. Please check your MongoDB connection and IP whitelist.", 'danger')
                return render_template('auth/register.html', active_tab=tab, patient_form=patient_form, doctor_form=doctor_form)

    return render_template(
        'auth/register.html',
        active_tab=tab,
        patient_form=patient_form,
        doctor_form=doctor_form
    )


@auth_bp.route('/logout')
def logout():
    csrf_tok = session.get('csrf_token')
    session.clear()
    if csrf_tok:
        session['csrf_token'] = csrf_tok
    flash('You have been safely logged out.', 'info')
    return redirect(url_for('main.index'))

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from repositories import user_repo, doctor_repo, patient_repo
from forms import LoginForm, RegisterPatientForm, RegisterDoctorForm

auth_bp = Blueprint('auth', __name__)

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
        session.clear()
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
            email = patient_form.email.data.strip().lower()
            if user_repo.get_by_email(email):
                flash('An account with this email address already exists. Please log in.', 'danger')
                return render_template('auth/register.html', active_tab=tab, patient_form=patient_form, doctor_form=doctor_form)

            # Create User
            new_user = user_repo.create({
                "name": patient_form.name.data.strip(),
                "email": email,
                "phone": patient_form.phone.data.strip(),
                "city": patient_form.city.data.strip(),
                "role": "patient",
                "password_hash": generate_password_hash(patient_form.password.data)
            })

            # Create Patient profile
            patient_repo.create({
                "user_id": new_user["id"],
                "name": new_user["name"],
                "email": new_user["email"],
                "phone": new_user["phone"],
                "city": new_user["city"]
            })

            # Auto login
            session.clear()
            session['user_id'] = new_user['id']
            session['user_role'] = 'patient'
            session['user_name'] = new_user['name']
            session['user_email'] = new_user['email']
            session.permanent = True

            flash('Welcome to FindMyDOC! Your patient account has been created.', 'success')
            return redirect(url_for('patient.dashboard'))

    # If doctor submission
    elif request.method == 'POST' and request.form.get('register_role') == 'doctor':
        tab = 'doctor'
        if doctor_form.validate_on_submit():
            email = doctor_form.email.data.strip().lower()
            if user_repo.get_by_email(email):
                flash('A doctor account with this email address already exists. Please log in.', 'danger')
                return render_template('auth/register.html', active_tab=tab, patient_form=patient_form, doctor_form=doctor_form)

            # Create User
            new_user = user_repo.create({
                "name": doctor_form.name.data.strip(),
                "email": email,
                "phone": doctor_form.phone.data.strip(),
                "city": doctor_form.city.data.strip(),
                "role": "doctor",
                "password_hash": generate_password_hash(doctor_form.password.data)
            })

            # Create Doctor Profile
            doctor_repo.create({
                "user_id": new_user["id"],
                "name": doctor_form.name.data.strip(),
                "email": email,
                "phone": doctor_form.phone.data.strip(),
                "city": doctor_form.city.data.strip(),
                "avatar": "/static/uploads/default_doctor.png",
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

            # Auto login
            session.clear()
            session['user_id'] = new_user['id']
            session['user_role'] = 'doctor'
            session['user_name'] = new_user['name']
            session['user_email'] = new_user['email']
            session.permanent = True

            flash('Welcome Dr. ' + new_user['name'] + '! Your professional doctor profile is ready.', 'success')
            return redirect(url_for('doctor.dashboard'))

    return render_template(
        'auth/register.html',
        active_tab=tab,
        patient_form=patient_form,
        doctor_form=doctor_form
    )


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been safely logged out.', 'info')
    return redirect(url_for('main.index'))

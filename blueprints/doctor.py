import os
from flask import Blueprint, render_template, redirect, url_for, flash, session, request, current_app
from werkzeug.utils import secure_filename
from utils.auth_decorators import role_required, get_current_user
from repositories import doctor_repo, appointment_repo, user_repo
from forms import DoctorProfileEditForm, DoctorAppointmentResponseForm

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')

def allowed_file(filename):
    allowed_exts = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts

@doctor_bp.route('/dashboard')
@role_required('doctor')
def dashboard():
    user = get_current_user()
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    doctor = doctor_repo.get_by_user_id(user['id'])
    if not doctor:
        flash('Doctor profile not found. Please set up your profile.', 'warning')
        return redirect(url_for('doctor.profile_edit'))

    doctor_id = doctor.get('id') if doctor else user['id']
    all_appointments = appointment_repo.get_by_doctor_id(doctor_id) if doctor_id else []

    pending_requests = [a for a in all_appointments if a.get('status') == 'Pending']
    upcoming_appointments = [a for a in all_appointments if a.get('status') == 'Confirmed']
    past_appointments = [a for a in all_appointments if a.get('status') in ['Rejected', 'Cancelled', 'Completed']]

    # Sort upcoming by assigned date
    upcoming_appointments.sort(key=lambda x: (x.get('assigned_date') or '', x.get('assigned_time') or ''))

    stats = {
        "pending_count": len(pending_requests),
        "confirmed_count": len(upcoming_appointments),
        "total_patients": len(all_appointments),
        "consultation_fee": doctor.get('consultation_fee', 0)
    }

    response_form = DoctorAppointmentResponseForm()

    return render_template(
        'doctor/dashboard.html',
        doctor=doctor,
        pending_requests=pending_requests,
        upcoming_appointments=upcoming_appointments,
        past_appointments=past_appointments,
        stats=stats,
        response_form=response_form
    )


@doctor_bp.route('/profile/edit', methods=['GET', 'POST'])
@role_required('doctor')
def profile_edit():
    user = get_current_user()
    doctor = doctor_repo.get_by_user_id(user['id'])
    if not doctor:
        # Create minimal placeholder doctor if none exists yet
        doctor = doctor_repo.create({
            "user_id": user['id'],
            "name": user['name'],
            "email": user['email'],
            "phone": user.get('phone', ''),
            "city": user.get('city', 'New York'),
            "specialization": "General Medicine",
            "doctor_type": "Hospital",
            "hospital_or_clinic_name": "General Medical Clinic",
            "qualifications": "MD",
            "experience_years": 5,
            "consultation_fee": 150.0,
            "address": "100 Medical Center Dr",
            "working_days": "Mon - Fri",
            "timings": "09:00 AM - 05:00 PM",
            "about": "Dedicated healthcare professional.",
            "avatar": "/static/uploads/default_doctor.png"
        })

    form = DoctorProfileEditForm(obj=type('obj', (object,), doctor))

    if form.validate_on_submit():
        updates = {
            "name": form.name.data.strip(),
            "phone": form.phone.data.strip(),
            "city": form.city.data.strip(),
            "specialization": form.specialization.data,
            "doctor_type": form.doctor_type.data,
            "hospital_or_clinic_name": form.hospital_or_clinic_name.data.strip(),
            "qualifications": form.qualifications.data.strip(),
            "experience_years": int(form.experience_years.data or 0),
            "consultation_fee": float(form.consultation_fee.data or 0),
            "address": form.address.data.strip(),
            "working_days": form.working_days.data.strip(),
            "timings": form.timings.data.strip(),
            "about": form.about.data.strip()
        }

        # Check for uploaded avatar
        if form.avatar_file.data:
            file = form.avatar_file.data
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
                saved_filename = f"doc_{doctor['id']}_{os.urandom(4).hex()}.{ext}"
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_filename)
                os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(upload_path)
                updates["avatar"] = f"/static/uploads/{saved_filename}"

        # Update Doctor repository
        doctor_repo.update(doctor['id'], updates)

        # Sync User repository name, phone & avatar
        user_updates = {
            "name": updates["name"],
            "phone": updates["phone"],
            "city": updates["city"]
        }
        if "avatar" in updates:
            user_updates["avatar"] = updates["avatar"]
            session['user_avatar'] = updates["avatar"]
        user_repo.update(user['id'], user_updates)
        session['user_name'] = updates["name"]

        flash('Your doctor profile has been updated successfully!', 'success')
        return redirect(url_for('doctor.dashboard'))

    elif request.method == 'GET':
        # Populate form fields with existing doctor values
        form.name.data = doctor.get('name')
        form.phone.data = doctor.get('phone')
        form.city.data = doctor.get('city')
        form.specialization.data = doctor.get('specialization')
        form.doctor_type.data = doctor.get('doctor_type')
        form.hospital_or_clinic_name.data = doctor.get('hospital_or_clinic_name')
        form.qualifications.data = doctor.get('qualifications')
        form.experience_years.data = doctor.get('experience_years')
        form.consultation_fee.data = doctor.get('consultation_fee')
        form.address.data = doctor.get('address')
        form.working_days.data = doctor.get('working_days')
        form.timings.data = doctor.get('timings')
        form.about.data = doctor.get('about')

    return render_template('doctor/profile_edit.html', form=form, doctor=doctor)

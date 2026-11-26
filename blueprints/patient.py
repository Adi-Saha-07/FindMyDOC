from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from utils.auth_decorators import role_required, get_current_user
from utils.image_utils import process_avatar_image
from repositories import patient_repo, appointment_repo, doctor_repo, user_repo
from forms import PatientProfileEditForm

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

@patient_bp.route('/dashboard')
@role_required('patient')
def dashboard():
    user = get_current_user()
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    patient = patient_repo.get_by_user_id(user['id'])
    if not patient:
        # Fallback create patient entry if missing
        patient = patient_repo.create({
            "user_id": user['id'],
            "name": user.get('name', 'Patient'),
            "email": user.get('email', ''),
            "phone": user.get('phone', ''),
            "city": user.get('city', 'Mumbai')
        })

    patient_id = patient.get('id') if patient else user['id']
    appointments = appointment_repo.get_by_patient_id(patient_id) if patient_id else []

    # Calculate statistics
    stats = {
        "total": len(appointments),
        "pending": sum(1 for a in appointments if a.get('status') == 'Pending'),
        "confirmed": sum(1 for a in appointments if a.get('status') == 'Confirmed'),
        "cancelled": sum(1 for a in appointments if a.get('status') in ['Cancelled', 'Rejected'])
    }

    # Enhance appointment objects with current doctor details if available
    enhanced_appointments = []
    for a in appointments:
        doc = doctor_repo.get_by_id(a.get('doctor_id'))
        item = dict(a)
        if doc:
            item['doctor_avatar'] = doc.get('avatar')
            item['doctor_address'] = doc.get('address')
            item['doctor_timings'] = doc.get('timings')
            item['doctor_fee'] = doc.get('consultation_fee')
        enhanced_appointments.append(item)

    return render_template(
        'patient/dashboard.html',
        patient=patient,
        appointments=enhanced_appointments,
        stats=stats
    )


@patient_bp.route('/cancel/<appointment_id>', methods=['POST'])
@role_required('patient')
def cancel_appointment(appointment_id):
    user = get_current_user()
    patient = patient_repo.get_by_user_id(user['id'])
    if not patient:
        flash('Patient record not found.', 'danger')
        return redirect(url_for('patient.dashboard'))

    success = appointment_repo.cancel_by_patient(appointment_id, patient['id'])
    if success:
        flash('Appointment request has been cancelled.', 'info')
    else:
        flash('Unable to cancel appointment. Only pending or confirmed appointments can be cancelled.', 'danger')

    return redirect(url_for('patient.dashboard'))


@patient_bp.route('/profile/edit', methods=['GET', 'POST'])
@role_required('patient')
def profile_edit():
    user = get_current_user()
    patient = patient_repo.get_by_user_id(user['id'])
    if not patient:
        patient = patient_repo.create({
            "user_id": user['id'],
            "name": user.get('name', 'Patient'),
            "email": user.get('email', ''),
            "phone": user.get('phone', ''),
            "city": user.get('city', 'Mumbai'),
            "avatar": "/static/uploads/default_patient.png"
        })

    form = PatientProfileEditForm()

    if form.validate_on_submit():
        updates = {
            "name": form.name.data.strip(),
            "phone": form.phone.data.strip(),
            "city": form.city.data.strip(),
        }

        # Avatar upload (serverless-safe base64)
        if form.avatar_file.data:
            avatar_data = process_avatar_image(form.avatar_file.data)
            if avatar_data:
                updates["avatar"] = avatar_data

        # Update patient record
        patient_repo.update(patient['id'], updates)

        # Sync user record
        user_updates = {"name": updates["name"], "phone": updates["phone"], "city": updates["city"]}
        if "avatar" in updates:
            user_updates["avatar"] = updates["avatar"]
        user_repo.update(user['id'], user_updates)

        # Update session
        session['user_name'] = updates["name"]
        if "avatar" in updates:
            session['user_avatar'] = updates["avatar"]

        flash('Your profile has been updated successfully!', 'success')
        return redirect(url_for('patient.profile_edit'))

    elif request.method == 'GET':
        form.name.data = patient.get('name') or user.get('name', '')
        form.phone.data = patient.get('phone') or user.get('phone', '')
        form.city.data = patient.get('city') or user.get('city', '')

    return render_template('patient/profile_edit.html', form=form, patient=patient)

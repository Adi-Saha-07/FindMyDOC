from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from utils.auth_decorators import login_required, role_required, get_current_user
from repositories import doctor_repo, patient_repo, appointment_repo
from forms import AppointmentRequestForm, DoctorAppointmentResponseForm

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')


@appointments_bp.route('/request/<doctor_id>', methods=['GET', 'POST'])
def request_appointment(doctor_id):
    # Ensure user is logged in as patient
    if 'user_id' not in session:
        flash('Please log in or register as a patient to request an appointment.', 'info')
        return redirect(url_for('auth.login', next=request.url))

    if session.get('user_role') != 'patient':
        flash('Doctors cannot book appointments. Please log in with a patient account.', 'warning')
        return redirect(url_for('doctor.dashboard'))

    doctor = doctor_repo.get_by_id(doctor_id)
    if not doctor:
        flash('The requested doctor was not found.', 'danger')
        return redirect(url_for('main.search'))

    user = get_current_user()
    patient = patient_repo.get_by_user_id(user['id'])
    if not patient:
        patient = patient_repo.create({
            "user_id": user['id'],
            "name": user['name'],
            "email": user['email'],
            "phone": user.get('phone', ''),
            "city": user.get('city', '')
        })

    form = AppointmentRequestForm()

    if form.validate_on_submit():
        new_appointment = {
            "patient_id": patient['id'],
            "patient_name": patient['name'],
            "patient_email": patient['email'],
            "patient_phone": patient.get('phone', ''),
            "doctor_id": doctor['id'],
            "doctor_name": doctor['name'],
            "doctor_specialization": doctor.get('specialization', ''),
            "hospital_or_clinic": doctor.get('hospital_or_clinic_name', ''),
            "city": doctor.get('city', ''),
            "preferred_date": form.preferred_date.data.strip() if form.preferred_date.data else None,
            "preferred_time": form.preferred_time.data,
            "reason": form.reason.data.strip(),
            "status": "Pending",
            "assigned_date": None,
            "assigned_time": None,
            "doctor_notes": None
        }

        created = appointment_repo.create(new_appointment)
        flash(f'Appointment request sent to {doctor["name"]}! Track status in your dashboard.', 'success')
        return redirect(url_for('patient.dashboard'))

    return render_template(
        'appointment_request.html',
        doctor=doctor,
        patient=patient,
        form=form
    )


@appointments_bp.route('/respond', methods=['POST'])
@role_required('doctor')
def respond_appointment():
    user = get_current_user()
    doctor = doctor_repo.get_by_user_id(user['id'])
    if not doctor:
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('doctor.dashboard'))

    form = DoctorAppointmentResponseForm()

    if form.validate_on_submit():
        appointment_id = form.appointment_id.data
        action = form.action.data.lower()
        appointment = appointment_repo.get_by_id(appointment_id)

        if not appointment or appointment.get('doctor_id') != doctor['id']:
            flash('Appointment request not found or unauthorized.', 'danger')
            return redirect(url_for('doctor.dashboard'))

        if action == 'accept':
            assigned_date = (form.assigned_date.data or '').strip()
            assigned_time = (form.assigned_time.data or '').strip()
            doctor_notes = (form.doctor_notes.data or '').strip()

            if not assigned_date or not assigned_time:
                flash('Please specify both a date and time slot to confirm the appointment.', 'warning')
                return redirect(url_for('doctor.dashboard'))

            # Check for double booking collision!
            if appointment_repo.is_slot_booked(doctor['id'], assigned_date, assigned_time, exclude_appointment_id=appointment_id):
                flash(f'Slot Conflict: You already have a confirmed appointment on {assigned_date} at {assigned_time}. Please pick another time.', 'danger')
                return redirect(url_for('doctor.dashboard'))

            # Update status to Confirmed
            appointment_repo.update_status(
                appointment_id=appointment_id,
                status="Confirmed",
                assigned_date=assigned_date,
                assigned_time=assigned_time,
                doctor_notes=doctor_notes
            )
            flash(f'Appointment with {appointment["patient_name"]} confirmed for {assigned_date} at {assigned_time}!', 'success')

        elif action == 'reject':
            doctor_notes = (form.doctor_notes.data or '').strip()
            appointment_repo.update_status(
                appointment_id=appointment_id,
                status="Rejected",
                doctor_notes=doctor_notes or "Doctor is unavailable during the requested period."
            )
            flash(f'Appointment request from {appointment["patient_name"]} has been declined.', 'info')

        else:
            flash('Invalid appointment action.', 'danger')

    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", 'danger')

    return redirect(url_for('doctor.dashboard'))

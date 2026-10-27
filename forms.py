from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, TextAreaField, SelectField,
    IntegerField, FloatField, HiddenField, SubmitField
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional

SPECIALIZATION_CHOICES = [
    ("Cardiology", "Cardiology"),
    ("Dermatology", "Dermatology"),
    ("Pediatrics", "Pediatrics"),
    ("Orthopedics", "Orthopedics"),
    ("Neurology", "Neurology"),
    ("General Medicine", "General Medicine"),
    ("Gynecology", "Gynecology"),
    ("Gastroenterology", "Gastroenterology"),
    ("Ophthalmology", "Ophthalmology"),
    ("Psychiatry", "Psychiatry"),
    ("ENT", "ENT (Ear, Nose & Throat)"),
    ("Oncology", "Oncology")
]

DOCTOR_TYPE_CHOICES = [
    ("Hospital", "Hospital Doctor"),
    ("Private", "Private Clinic / Independent")
]

class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Login As', choices=[
        ('auto', 'Auto-Detect Role'),
        ('patient', 'Patient'),
        ('doctor', 'Doctor')
    ], default='auto')
    submit = SubmitField('Sign In')


class RegisterPatientForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=7, max=20)])
    city = StringField('City', validators=[DataRequired(), Length(min=2, max=60)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters")])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match")])
    submit = SubmitField('Create Patient Account')


class RegisterDoctorForm(FlaskForm):
    name = StringField('Doctor Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Professional Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=7, max=20)])
    city = StringField('City', validators=[DataRequired(), Length(min=2, max=60)])
    specialization = SelectField('Specialization', choices=SPECIALIZATION_CHOICES, validators=[DataRequired()])
    doctor_type = SelectField('Doctor Type', choices=DOCTOR_TYPE_CHOICES, validators=[DataRequired()])
    hospital_or_clinic_name = StringField('Hospital or Clinic Name', validators=[DataRequired(), Length(min=2, max=120)])
    qualifications = StringField('Qualifications (e.g., MD, FACS)', validators=[DataRequired(), Length(min=2, max=120)])
    experience_years = IntegerField('Years of Experience', validators=[DataRequired(), NumberRange(min=0, max=60)])
    consultation_fee = FloatField('Consultation Fee ($ USD)', validators=[DataRequired(), NumberRange(min=0, max=2000)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters")])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match")])
    submit = SubmitField('Register as Doctor')


class DoctorProfileEditForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone Number', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    specialization = SelectField('Specialization', choices=SPECIALIZATION_CHOICES, validators=[DataRequired()])
    doctor_type = SelectField('Practice Type', choices=DOCTOR_TYPE_CHOICES, validators=[DataRequired()])
    hospital_or_clinic_name = StringField('Hospital / Clinic Name', validators=[DataRequired()])
    qualifications = StringField('Qualifications & Degrees', validators=[DataRequired()])
    experience_years = IntegerField('Years of Experience', validators=[DataRequired(), NumberRange(min=0, max=60)])
    consultation_fee = FloatField('Consultation Fee ($ USD)', validators=[DataRequired(), NumberRange(min=0, max=3000)])
    address = StringField('Clinic / Hospital Address', validators=[DataRequired()])
    working_days = StringField('Working Days (e.g., Mon - Fri)', validators=[DataRequired()])
    timings = StringField('Daily Timings (e.g., 09:00 AM - 05:00 PM)', validators=[DataRequired()])
    about = TextAreaField('About & Bio', validators=[DataRequired(), Length(min=20, max=1500)])
    avatar_file = FileField('Profile Photo', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only (jpg, png, webp)')])
    submit = SubmitField('Save Profile Changes')


class AppointmentRequestForm(FlaskForm):
    preferred_date = StringField('Preferred Date', validators=[Optional()])
    preferred_time = SelectField('Preferred Time of Day', choices=[
        ('Anytime', 'Anytime during office hours'),
        ('Morning', 'Morning (08:00 AM - 12:00 PM)'),
        ('Afternoon', 'Afternoon (12:00 PM - 04:00 PM)'),
        ('Evening', 'Evening (04:00 PM - 07:00 PM)')
    ], default='Anytime')
    reason = TextAreaField('Reason for Visit / Symptoms', validators=[
        DataRequired(),
        Length(min=5, max=1000, message="Please describe your health query in 5 to 1000 characters.")
    ])
    submit = SubmitField('Submit Appointment Request')


class DoctorAppointmentResponseForm(FlaskForm):
    appointment_id = HiddenField('Appointment ID', validators=[DataRequired()])
    action = HiddenField('Action', validators=[DataRequired()])  # 'accept' or 'reject'
    assigned_date = StringField('Scheduled Date')
    assigned_time = StringField('Scheduled Time Slot')
    doctor_notes = TextAreaField('Doctor Note to Patient')
    submit = SubmitField('Confirm Decision')

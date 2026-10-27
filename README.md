# FindMyDOC
### Clean & Professional Doctor-Finder & Confirmed Appointment Booking Platform

FindMyDOC is a full-stack healthcare web application built with **Python Flask** and **server-rendered Jinja2 templates**, featuring a clean, minimalist design system based on **Sage Green and Crisp White** (Light Mode) and **Solid Black and Sage Green** (Dark Mode).

---

## 🌟 Key Features

### For Patients
- **City Search with Instant Autocomplete**: Enter any city (e.g., New York, Chicago, San Francisco) with dynamic suggestions backed by seed data.
- **Multidimensional Filters**: Filter by Medical Specialization, Doctor Type (Hospital-Affiliated vs. Private Practice), and Consultation Fee Range ($), with sorting by rating, experience, or price.
- **Doctor Profiles**: Comprehensive doctor details including qualifications, experience, hospital affiliation, clinic address, working days, daily hours, fee, and verified patient reviews.
- **Appointment Requests**: Submit consultation requests with health concerns/symptoms, preferred visit dates, and time windows.
- **Real-Time Patient Dashboard**: Track live status (`Pending`, `Confirmed`, `Rejected`, `Cancelled`), view doctor-assigned confirmed date & time slots, read clinical prep instructions, and cancel pending requests.

### For Doctors
- **Dedicated Doctor Portal**: Separate login, role verification, and access protection.
- **Interactive Dashboard**: View incoming patient requests with symptoms and contact details.
- **Accept with Date/Time Picker**: Confirm appointments by choosing an exact date and time slot with custom patient notes.
- **Double-Booking Collision Prevention**: The platform enforces validation that prevents a doctor from being double-booked on the same date and time slot.
- **Doctor Profile Management**: Edit credentials, hospital/clinic name, address, working days, daily consultation hours, fee, bio, and upload custom profile photos (stored locally in `/static/uploads`).

### Liquid Glassmorphism Design System
- Translucent frosted glass cards with `backdrop-filter: blur(20px) saturate(180%)`, soft inner highlights, and layered shadows.
- Animated fluid gradient background with morphing SVG blobs in healthcare teal, blue, and indigo tones.
- SVG noise texture overlay for genuine physical glass depth.
- Light-sweep glossy hover animations on cards and interactive elements.
- Full **Light & Dark mode** with smooth theme switcher persisted in `localStorage`.
- Fully responsive (mobile-first) with accessible color contrast and `prefers-reduced-motion` compliance.

---

## 🏗️ Clean Repository Architecture & MongoDB Migration Guide

The application strictly implements the **Repository Pattern** (`BaseUserRepository`, `BaseDoctorRepository`, `BasePatientRepository`, `BaseAppointmentRepository`). All state is managed through the abstract interface, backed by an in-memory data store seeded from `data/seed.json`.

### Plug-and-Play MongoDB Switch
To switch from in-memory storage to MongoDB (via PyMongo):
1. Install PyMongo:
   ```bash
   pip install pymongo dnspython
   ```
2. Configure MongoDB connection in `.env` or environment variables:
   ```env
   MONGO_URI="mongodb+srv://<user>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority"
   DATABASE_NAME="mediconnect"
   ```
3. In `repositories/__init__.py`, replace `InMemory*Repository` with `Mongo*Repository` from `repositories/mongo_repository.py`.

### Planned MongoDB Schema & Indexes

#### 1. `users` Collection
- **Fields**: `_id` (ObjectId), `name` (String), `email` (String), `phone` (String), `city` (String), `role` ("patient" | "doctor"), `password_hash` (String), `created_at` (ISODate).
- **Indexes**:
  - `{"email": 1}` — Unique index for authentication lookups.
  - `{"role": 1}` — Role filtering index.

#### 2. `doctors` Collection
- **Fields**: `_id` (ObjectId), `user_id` (String / ObjectId), `name` (String), `email` (String), `phone` (String), `avatar` (String), `specialization` (String), `qualifications` (String), `experience_years` (Int), `doctor_type` ("Hospital" | "Private"), `hospital_or_clinic_name` (String), `address` (String), `city` (String), `consultation_fee` (Double), `working_days` (String), `timings` (String), `about` (String), `rating` (Double), `review_count` (Int).
- **Indexes**:
  - `{"city": 1, "specialization": 1, "doctor_type": 1}` — Compound search index for query execution.
  - Text Index on `$**` or `{"name": "text", "specialization": "text", "hospital_or_clinic_name": "text", "about": "text"}` for keyword full-text search.
  - `{"consultation_fee": 1, "rating": -1}` — Sort and fee range index.
  - `{"user_id": 1}` — Unique index linking user identity.

#### 3. `patients` Collection
- **Fields**: `_id` (ObjectId), `user_id` (String / ObjectId), `name` (String), `email` (String), `phone` (String), `city` (String).
- **Indexes**:
  - `{"user_id": 1}` — Unique index.
  - `{"email": 1}` — Quick lookup index.

#### 4. `appointments` Collection
- **Fields**: `_id` (ObjectId), `patient_id` (String), `patient_name` (String), `patient_email` (String), `patient_phone` (String), `doctor_id` (String), `doctor_name` (String), `doctor_specialization` (String), `hospital_or_clinic` (String), `city` (String), `preferred_date` (String), `preferred_time` (String), `reason` (String), `status` ("Pending" | "Confirmed" | "Rejected" | "Cancelled"), `assigned_date` (String), `assigned_time` (String), `doctor_notes` (String), `created_at` (ISODate).
- **Indexes**:
  - `{"doctor_id": 1, "assigned_date": 1, "assigned_time": 1, "status": 1}` — Compound collision prevention index.
  - `{"patient_id": 1, "created_at": -1}` — Patient dashboard history lookup.
  - `{"doctor_id": 1, "status": 1, "created_at": -1}` — Doctor incoming requests and scheduled appointments query index.

---

## 🚀 Setup & Run Instructions

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Pip

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python app.py
```
The server will start at `http://127.0.0.1:5000`.

---

## 🔑 Demo Credentials

MediConnect is pre-seeded with 16 doctors across 6 cities, realistic patient records, and existing appointments:

| Role | Email | Password | Details |
| :--- | :--- | :--- | :--- |
| **Patient (Mariz)** | `mariz@mediconnect.com` | `Patient@123` | Pre-booked appointment with Dr. Jenkins |
| **Doctor (Dr. Sarah)** | `dr.sarah@mediconnect.com` | `Doctor@123` | Cardiologist at Mount Sinai, New York |
| **Doctor (Dr. Marcus)** | `dr.marcus@mediconnect.com` | `Doctor@123` | Dermatologist at Lumina Clinic, New York |
| **Doctor (Dr. Elena)** | `dr.elena@mediconnect.com` | `Doctor@123` | Pediatrician at UCSF, San Francisco |

*Tip: The Sign In page features one-click demo account auto-fill buttons for quick testing!*

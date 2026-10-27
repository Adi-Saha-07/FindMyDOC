import json
import os
import uuid
import threading
from datetime import datetime
from typing import List, Optional, Dict, Any
from repositories.base import (
    BaseUserRepository,
    BaseDoctorRepository,
    BasePatientRepository,
    BaseAppointmentRepository
)

class InMemoryDataStore:
    """
    In-memory storage holding users, doctors, patients, and appointments.
    Loaded from data/seed.json on application startup.
    Thread-safe mutations via threading.RLock.
    """
    _instance = None
    _lock = threading.RLock()

    def __init__(self, seed_file_path: str):
        self.seed_file_path = seed_file_path
        self.users: Dict[str, Dict[str, Any]] = {}
        self.doctors: Dict[str, Dict[str, Any]] = {}
        self.patients: Dict[str, Dict[str, Any]] = {}
        self.appointments: Dict[str, Dict[str, Any]] = {}
        self.cities: List[str] = []
        self.specializations: List[str] = []
        self.load_seed_data()

    def load_seed_data(self):
        with self._lock:
            if not os.path.exists(self.seed_file_path):
                return
            with open(self.seed_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.cities = list(data.get("cities", []))
            self.specializations = list(data.get("specializations", []))

            for u in data.get("users", []):
                self.users[u["id"]] = dict(u)

            for d in data.get("doctors", []):
                self.doctors[d["id"]] = dict(d)

            for p in data.get("patients", []):
                self.patients[p["id"]] = dict(p)

            for a in data.get("appointments", []):
                self.appointments[a["id"]] = dict(a)


# Singleton factory or holder
_datastore_instance: Optional[InMemoryDataStore] = None

def get_datastore(seed_path: Optional[str] = None) -> InMemoryDataStore:
    global _datastore_instance
    if _datastore_instance is None:
        if seed_path is None:
            seed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "seed.json")
        _datastore_instance = InMemoryDataStore(seed_path)
    return _datastore_instance


class InMemoryUserRepository(BaseUserRepository):
    def __init__(self, datastore: Optional[InMemoryDataStore] = None):
        self.ds = datastore or get_datastore()

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self.ds._lock:
            user = self.ds.users.get(user_id)
            return dict(user) if user else None

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self.ds._lock:
            target = email.strip().lower()
            for user in self.ds.users.values():
                if user.get("email", "").strip().lower() == target:
                    return dict(user)
            return None

    def create(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        with self.ds._lock:
            user_id = user_data.get("id") or f"u-{uuid.uuid4().hex[:8]}"
            new_user = dict(user_data)
            new_user["id"] = user_id
            new_user["email"] = new_user.get("email", "").strip().lower()
            new_user["created_at"] = new_user.get("created_at") or datetime.utcnow().isoformat() + "Z"
            self.ds.users[user_id] = new_user
            return dict(new_user)

    def update(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self.ds._lock:
            if user_id not in self.ds.users:
                return None
            user = self.ds.users[user_id]
            for k, v in updates.items():
                if k != "id":
                    user[k] = v
            return dict(user)


class InMemoryDoctorRepository(BaseDoctorRepository):
    def __init__(self, datastore: Optional[InMemoryDataStore] = None):
        self.ds = datastore or get_datastore()

    def get_by_id(self, doctor_id: str) -> Optional[Dict[str, Any]]:
        with self.ds._lock:
            doc = self.ds.doctors.get(doctor_id)
            return dict(doc) if doc else None

    def get_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self.ds._lock:
            for doc in self.ds.doctors.values():
                if doc.get("user_id") == user_id:
                    return dict(doc)
            return None

    def search(
        self,
        city: Optional[str] = None,
        specialization: Optional[str] = None,
        doctor_type: Optional[str] = None,
        min_fee: Optional[float] = None,
        max_fee: Optional[float] = None,
        sort_by: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with self.ds._lock:
            results = list(self.ds.doctors.values())

            # City match (case-insensitive)
            if city and city.strip():
                c_clean = city.strip().lower()
                results = [d for d in results if d.get("city", "").strip().lower() == c_clean]

            # Specialization match
            if specialization and specialization.strip() and specialization != "all":
                spec_clean = specialization.strip().lower()
                results = [d for d in results if d.get("specialization", "").strip().lower() == spec_clean]

            # Doctor type match (Hospital / Private)
            if doctor_type and doctor_type.strip() and doctor_type != "all":
                dtype_clean = doctor_type.strip().lower()
                results = [d for d in results if d.get("doctor_type", "").strip().lower() == dtype_clean]

            # Fees range
            if min_fee is not None:
                results = [d for d in results if float(d.get("consultation_fee", 0)) >= min_fee]
            if max_fee is not None:
                results = [d for d in results if float(d.get("consultation_fee", 0)) <= max_fee]

            # Keyword search term (matches name, hospital, specialization, about)
            if search_term and search_term.strip():
                term = search_term.strip().lower()
                results = [
                    d for d in results
                    if term in d.get("name", "").lower()
                    or term in d.get("specialization", "").lower()
                    or term in d.get("hospital_or_clinic_name", "").lower()
                    or term in d.get("about", "").lower()
                ]

            # Sorting
            if sort_by == "rating":
                results.sort(key=lambda x: (float(x.get("rating", 0)), int(x.get("review_count", 0))), reverse=True)
            elif sort_by == "experience":
                results.sort(key=lambda x: int(x.get("experience_years", 0)), reverse=True)
            elif sort_by == "fee_asc":
                results.sort(key=lambda x: float(x.get("consultation_fee", 0)))
            elif sort_by == "fee_desc":
                results.sort(key=lambda x: float(x.get("consultation_fee", 0)), reverse=True)
            else:
                # Default: sort by highest rating
                results.sort(key=lambda x: float(x.get("rating", 0)), reverse=True)

            return [dict(d) for d in results]

    def get_all_cities(self) -> List[str]:
        with self.ds._lock:
            # Union of known cities list and doctor cities
            cities_set = set(self.ds.cities)
            for doc in self.ds.doctors.values():
                c = doc.get("city")
                if c:
                    cities_set.add(c)
            return sorted(list(cities_set))

    def get_all_specializations(self) -> List[str]:
        with self.ds._lock:
            specs = set(self.ds.specializations)
            for doc in self.ds.doctors.values():
                s = doc.get("specialization")
                if s:
                    specs.add(s)
            return sorted(list(specs))

    def create(self, doctor_data: Dict[str, Any]) -> Dict[str, Any]:
        with self.ds._lock:
            doc_id = doctor_data.get("id") or f"doc-{uuid.uuid4().hex[:8]}"
            new_doc = dict(doctor_data)
            new_doc["id"] = doc_id
            new_doc.setdefault("rating", 5.0)
            new_doc.setdefault("review_count", 1)
            self.ds.doctors[doc_id] = new_doc
            # Add city to cities if not present
            if new_doc.get("city") and new_doc["city"] not in self.ds.cities:
                self.ds.cities.append(new_doc["city"])
            # Add spec to specs if not present
            if new_doc.get("specialization") and new_doc["specialization"] not in self.ds.specializations:
                self.ds.specializations.append(new_doc["specialization"])
            return dict(new_doc)

    def update(self, doctor_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self.ds._lock:
            if doctor_id not in self.ds.doctors:
                return None
            doc = self.ds.doctors[doctor_id]
            for k, v in updates.items():
                if k != "id":
                    doc[k] = v
            if doc.get("city") and doc["city"] not in self.ds.cities:
                self.ds.cities.append(doc["city"])
            return dict(doc)


class InMemoryPatientRepository(BasePatientRepository):
    def __init__(self, datastore: Optional[InMemoryDataStore] = None):
        self.ds = datastore or get_datastore()

    def get_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        with self.ds._lock:
            p = self.ds.patients.get(patient_id)
            return dict(p) if p else None

    def get_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self.ds._lock:
            for p in self.ds.patients.values():
                if p.get("user_id") == user_id:
                    return dict(p)
            return None

    def create(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        with self.ds._lock:
            pat_id = patient_data.get("id") or f"pat-{uuid.uuid4().hex[:8]}"
            new_pat = dict(patient_data)
            new_pat["id"] = pat_id
            self.ds.patients[pat_id] = new_pat
            return dict(new_pat)

    def update(self, patient_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self.ds._lock:
            if patient_id not in self.ds.patients:
                return None
            pat = self.ds.patients[patient_id]
            for k, v in updates.items():
                if k != "id":
                    pat[k] = v
            return dict(pat)


class InMemoryAppointmentRepository(BaseAppointmentRepository):
    def __init__(self, datastore: Optional[InMemoryDataStore] = None):
        self.ds = datastore or get_datastore()

    def get_by_id(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        with self.ds._lock:
            apt = self.ds.appointments.get(appointment_id)
            return dict(apt) if apt else None

    def get_by_patient_id(self, patient_id: str) -> List[Dict[str, Any]]:
        with self.ds._lock:
            apts = [a for a in self.ds.appointments.values() if a.get("patient_id") == patient_id]
            # Order newest first
            apts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return [dict(a) for a in apts]

    def get_by_doctor_id(self, doctor_id: str) -> List[Dict[str, Any]]:
        with self.ds._lock:
            apts = [a for a in self.ds.appointments.values() if a.get("doctor_id") == doctor_id]
            apts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return [dict(a) for a in apts]

    def create(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        with self.ds._lock:
            apt_id = appointment_data.get("id") or f"apt-{uuid.uuid4().hex[:8]}"
            new_apt = dict(appointment_data)
            new_apt["id"] = apt_id
            new_apt.setdefault("status", "Pending")
            new_apt.setdefault("created_at", datetime.utcnow().isoformat() + "Z")
            new_apt.setdefault("assigned_date", None)
            new_apt.setdefault("assigned_time", None)
            new_apt.setdefault("doctor_notes", None)
            self.ds.appointments[apt_id] = new_apt
            return dict(new_apt)

    def update_status(
        self,
        appointment_id: str,
        status: str,
        assigned_date: Optional[str] = None,
        assigned_time: Optional[str] = None,
        doctor_notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        with self.ds._lock:
            if appointment_id not in self.ds.appointments:
                return None
            apt = self.ds.appointments[appointment_id]
            apt["status"] = status
            if assigned_date is not None:
                apt["assigned_date"] = assigned_date
            if assigned_time is not None:
                apt["assigned_time"] = assigned_time
            if doctor_notes is not None:
                apt["doctor_notes"] = doctor_notes
            return dict(apt)

    def cancel_by_patient(self, appointment_id: str, patient_id: str) -> bool:
        with self.ds._lock:
            apt = self.ds.appointments.get(appointment_id)
            if not apt:
                return False
            # Only the patient who booked can cancel, and only when Pending or Confirmed
            if apt.get("patient_id") == patient_id and apt.get("status") in ["Pending", "Confirmed"]:
                apt["status"] = "Cancelled"
                return True
            return False

    def is_slot_booked(
        self,
        doctor_id: str,
        assigned_date: str,
        assigned_time: str,
        exclude_appointment_id: Optional[str] = None
    ) -> bool:
        """
        Prevents double-booking: Checks if doctor already has a Confirmed appointment
        on the exact same date and time.
        """
        with self.ds._lock:
            date_clean = assigned_date.strip()
            time_clean = assigned_time.strip().lower()
            for apt in self.ds.appointments.values():
                if apt.get("doctor_id") == doctor_id and apt.get("status") == "Confirmed":
                    if exclude_appointment_id and apt.get("id") == exclude_appointment_id:
                        continue
                    a_date = (apt.get("assigned_date") or "").strip()
                    a_time = (apt.get("assigned_time") or "").strip().lower()
                    if a_date == date_clean and a_time == time_clean:
                        return True
            return False

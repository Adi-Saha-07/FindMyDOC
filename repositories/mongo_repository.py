"""
MongoDB Repository Implementation for FindMyDOC using PyMongo.
==============================================================
Provides fully implemented MongoDB persistence for users, doctors,
patients, and appointments.
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pymongo import MongoClient, ASCENDING, DESCENDING

from repositories.base import (
    BaseUserRepository,
    BaseDoctorRepository,
    BasePatientRepository,
    BaseAppointmentRepository
)

class MongoDatabaseClient:
    """Singleton MongoDB Client connection wrapper with auto-indexing."""
    _instance = None

    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self.uri = uri or os.environ.get("MONGO_URI", "mongodb://localhost:27017/findmydoc")
        self.db_name = db_name or os.environ.get("DATABASE_NAME", "findmydoc")
        
        client_options: Dict[str, Any] = {
            "serverSelectionTimeoutMS": 2000,
            "connectTimeoutMS": 2000,
            "socketTimeoutMS": 2000,
            "retryWrites": True,
        }
        try:
            import certifi
            client_options["tlsCAFile"] = certifi.where()
        except Exception:
            pass

        self.client = MongoClient(self.uri, **client_options)
        self.db = self.client[self.db_name]
        self._ensure_indexes()

    def _ensure_indexes(self):
        try:
            # Users
            self.db.users.create_index([("email", ASCENDING)], unique=True)
            self.db.users.create_index([("role", ASCENDING)])

            # Doctors
            self.db.doctors.create_index([("city", ASCENDING), ("specialization", ASCENDING)])
            self.db.doctors.create_index([("user_id", ASCENDING)], unique=True)
            self.db.doctors.create_index([("consultation_fee", ASCENDING), ("rating", DESCENDING)])

            # Patients
            self.db.patients.create_index([("user_id", ASCENDING)], unique=True)

            # Appointments
            self.db.appointments.create_index([
                ("doctor_id", ASCENDING),
                ("assigned_date", ASCENDING),
                ("assigned_time", ASCENDING),
                ("status", ASCENDING)
            ])
            self.db.appointments.create_index([("patient_id", ASCENDING), ("created_at", DESCENDING)])
            self.db.appointments.create_index([("doctor_id", ASCENDING), ("created_at", DESCENDING)])
        except Exception as e:
            print(f"[MongoDB] Notice: Could not ensure indexes right now ({e}).")

    @classmethod
    def get_instance(cls, uri: Optional[str] = None, db_name: Optional[str] = None):
        if cls._instance is None:
            cls._instance = cls(uri, db_name)
        return cls._instance


def _clean_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Clean MongoDB document by ensuring standard string 'id' field."""
    if not doc:
        return None
    d = dict(doc)
    if "_id" in d and "id" not in d:
        d["id"] = str(d["_id"])
    elif "_id" in d and isinstance(d["_id"], str) and "id" not in d:
        d["id"] = d["_id"]
    return d


class MongoUserRepository(BaseUserRepository):
    def __init__(self, db_client: Optional[MongoDatabaseClient] = None):
        self.db_client = db_client or MongoDatabaseClient.get_instance()
        self.col = self.db_client.db.users

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        doc = self.col.find_one({"$or": [{"_id": user_id}, {"id": user_id}]})
        return _clean_doc(doc)

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        target = email.strip().lower()
        doc = self.col.find_one({"email": target})
        return _clean_doc(doc)

    def create(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = user_data.get("id") or f"u-{uuid.uuid4().hex[:8]}"
        new_user = dict(user_data)
        new_user["id"] = user_id
        new_user["_id"] = user_id
        new_user["email"] = new_user.get("email", "").strip().lower()
        new_user["created_at"] = new_user.get("created_at") or datetime.utcnow().isoformat() + "Z"
        self.col.insert_one(new_user)
        return _clean_doc(new_user)

    def update(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        clean_updates = {k: v for k, v in updates.items() if k not in ["_id", "id"]}
        doc = self.col.find_one_and_update(
            {"$or": [{"_id": user_id}, {"id": user_id}]},
            {"$set": clean_updates},
            return_document=True
        )
        return _clean_doc(doc)


class MongoDoctorRepository(BaseDoctorRepository):
    def __init__(self, db_client: Optional[MongoDatabaseClient] = None):
        self.db_client = db_client or MongoDatabaseClient.get_instance()
        self.col = self.db_client.db.doctors

    def get_by_id(self, doctor_id: str) -> Optional[Dict[str, Any]]:
        doc = self.col.find_one({"$or": [{"_id": doctor_id}, {"id": doctor_id}]})
        return _clean_doc(doc)

    def get_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        doc = self.col.find_one({"user_id": user_id})
        return _clean_doc(doc)

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
        query: Dict[str, Any] = {}

        if city and city.strip():
            query["city"] = {"$regex": f"^{city.strip()}$", "$options": "i"}

        if specialization and specialization.strip() and specialization != "all":
            query["specialization"] = {"$regex": f"^{specialization.strip()}$", "$options": "i"}

        if doctor_type and doctor_type.strip() and doctor_type != "all":
            query["doctor_type"] = {"$regex": f"^{doctor_type.strip()}$", "$options": "i"}

        fee_filter = {}
        if min_fee is not None:
            fee_filter["$gte"] = float(min_fee)
        if max_fee is not None:
            fee_filter["$lte"] = float(max_fee)
        if fee_filter:
            query["consultation_fee"] = fee_filter

        if search_term and search_term.strip():
            st = search_term.strip()
            query["$or"] = [
                {"name": {"$regex": st, "$options": "i"}},
                {"specialization": {"$regex": st, "$options": "i"}},
                {"hospital_or_clinic_name": {"$regex": st, "$options": "i"}},
                {"about": {"$regex": st, "$options": "i"}}
            ]

        cursor = self.col.find(query)

        # Sorting
        if sort_by == "rating":
            cursor = cursor.sort([("rating", DESCENDING), ("review_count", DESCENDING)])
        elif sort_by == "experience":
            cursor = cursor.sort([("experience_years", DESCENDING)])
        elif sort_by == "fee_asc":
            cursor = cursor.sort([("consultation_fee", ASCENDING)])
        elif sort_by == "fee_desc":
            cursor = cursor.sort([("consultation_fee", DESCENDING)])
        else:
            cursor = cursor.sort([("rating", DESCENDING)])

        return [_clean_doc(d) for d in cursor]

    def get_all_cities(self) -> List[str]:
        default_cities = [
            "Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad",
            "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Surat"
        ]
        cities = set(self.col.distinct("city"))
        cities.update(default_cities)
        return sorted([c for c in cities if c])

    def get_all_specializations(self) -> List[str]:
        default_specs = [
            "Cardiology", "Dermatology", "Pediatrics", "Orthopedics",
            "Neurology", "General Medicine", "Gynecology", "Gastroenterology"
        ]
        specs = set(self.col.distinct("specialization"))
        specs.update(default_specs)
        return sorted([s for s in specs if s])

    def create(self, doctor_data: Dict[str, Any]) -> Dict[str, Any]:
        doc_id = doctor_data.get("id") or f"doc-{uuid.uuid4().hex[:8]}"
        new_doc = dict(doctor_data)
        new_doc["id"] = doc_id
        new_doc["_id"] = doc_id
        new_doc.setdefault("rating", 5.0)
        new_doc.setdefault("review_count", 1)
        self.col.insert_one(new_doc)
        return _clean_doc(new_doc)

    def update(self, doctor_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        clean_updates = {k: v for k, v in updates.items() if k not in ["_id", "id"]}
        doc = self.col.find_one_and_update(
            {"$or": [{"_id": doctor_id}, {"id": doctor_id}]},
            {"$set": clean_updates},
            return_document=True
        )
        return _clean_doc(doc)


class MongoPatientRepository(BasePatientRepository):
    def __init__(self, db_client: Optional[MongoDatabaseClient] = None):
        self.db_client = db_client or MongoDatabaseClient.get_instance()
        self.col = self.db_client.db.patients

    def get_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        doc = self.col.find_one({"$or": [{"_id": patient_id}, {"id": patient_id}]})
        return _clean_doc(doc)

    def get_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        doc = self.col.find_one({"user_id": user_id})
        return _clean_doc(doc)

    def create(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        pat_id = patient_data.get("id") or f"pat-{uuid.uuid4().hex[:8]}"
        new_pat = dict(patient_data)
        new_pat["id"] = pat_id
        new_pat["_id"] = pat_id
        self.col.insert_one(new_pat)
        return _clean_doc(new_pat)

    def update(self, patient_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        clean_updates = {k: v for k, v in updates.items() if k not in ["_id", "id"]}
        doc = self.col.find_one_and_update(
            {"$or": [{"_id": patient_id}, {"id": patient_id}]},
            {"$set": clean_updates},
            return_document=True
        )
        return _clean_doc(doc)


class MongoAppointmentRepository(BaseAppointmentRepository):
    def __init__(self, db_client: Optional[MongoDatabaseClient] = None):
        self.db_client = db_client or MongoDatabaseClient.get_instance()
        self.col = self.db_client.db.appointments

    def get_by_id(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        doc = self.col.find_one({"$or": [{"_id": appointment_id}, {"id": appointment_id}]})
        return _clean_doc(doc)

    def get_by_patient_id(self, patient_id: str) -> List[Dict[str, Any]]:
        cursor = self.col.find({"patient_id": patient_id}).sort([("created_at", DESCENDING)])
        return [_clean_doc(d) for d in cursor]

    def get_by_doctor_id(self, doctor_id: str) -> List[Dict[str, Any]]:
        cursor = self.col.find({"doctor_id": doctor_id}).sort([("created_at", DESCENDING)])
        return [_clean_doc(d) for d in cursor]

    def create(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        apt_id = appointment_data.get("id") or f"apt-{uuid.uuid4().hex[:8]}"
        new_apt = dict(appointment_data)
        new_apt["id"] = apt_id
        new_apt["_id"] = apt_id
        new_apt.setdefault("status", "Pending")
        new_apt.setdefault("created_at", datetime.utcnow().isoformat() + "Z")
        new_apt.setdefault("assigned_date", None)
        new_apt.setdefault("assigned_time", None)
        new_apt.setdefault("doctor_notes", None)
        self.col.insert_one(new_apt)
        return _clean_doc(new_apt)

    def update_status(
        self,
        appointment_id: str,
        status: str,
        assigned_date: Optional[str] = None,
        assigned_time: Optional[str] = None,
        doctor_notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        updates = {"status": status}
        if assigned_date is not None:
            updates["assigned_date"] = assigned_date
        if assigned_time is not None:
            updates["assigned_time"] = assigned_time
        if doctor_notes is not None:
            updates["doctor_notes"] = doctor_notes

        doc = self.col.find_one_and_update(
            {"$or": [{"_id": appointment_id}, {"id": appointment_id}]},
            {"$set": updates},
            return_document=True
        )
        return _clean_doc(doc)

    def cancel_by_patient(self, appointment_id: str, patient_id: str) -> bool:
        doc = self.col.find_one({"$or": [{"_id": appointment_id}, {"id": appointment_id}]})
        if not doc:
            return False
        if doc.get("patient_id") == patient_id and doc.get("status") in ["Pending", "Confirmed"]:
            self.col.update_one(
                {"$or": [{"_id": appointment_id}, {"id": appointment_id}]},
                {"$set": {"status": "Cancelled"}}
            )
            return True
        return False

    def is_slot_booked(
        self,
        doctor_id: str,
        assigned_date: str,
        assigned_time: str,
        exclude_appointment_id: Optional[str] = None
    ) -> bool:
        """Double-booking prevention: check for matching doctor, date, time and Confirmed status."""
        query = {
            "doctor_id": doctor_id,
            "status": "Confirmed",
            "assigned_date": assigned_date.strip(),
            "assigned_time": {"$regex": f"^{assigned_time.strip()}$", "$options": "i"}
        }
        if exclude_appointment_id:
            query["$and"] = [
                {"_id": {"$ne": exclude_appointment_id}},
                {"id": {"$ne": exclude_appointment_id}}
            ]

        existing = self.col.find_one(query)
        return existing is not None

"""
Repository layer provider for FindMyDOC.
========================================
Supports dual backends:
1. In-Memory (default, zero-setup, pre-seeded from data/seed.json)
2. MongoDB (production database via PyMongo)

To activate MongoDB:
  Set environment variable DATA_BACKEND=mongodb
  Optionally set MONGO_URI="mongodb://localhost:27017/findmydoc" or your Atlas connection string.
"""

import os
from repositories.in_memory import (
    InMemoryUserRepository,
    InMemoryDoctorRepository,
    InMemoryPatientRepository,
    InMemoryAppointmentRepository,
    get_datastore
)

backend_choice = os.environ.get("DATA_BACKEND")
if not backend_choice:
    backend_choice = "mongodb" if os.environ.get("MONGO_URI") else "memory"
backend_choice = backend_choice.strip().lower()

use_mongo = False
if backend_choice == "mongodb":
    try:
        from repositories.mongo_repository import (
            MongoUserRepository,
            MongoDoctorRepository,
            MongoPatientRepository,
            MongoAppointmentRepository,
            MongoDatabaseClient
        )
        # Test connection
        client = MongoDatabaseClient.get_instance()
        client.db.command('ping')
        
        user_repo = MongoUserRepository(client)
        doctor_repo = MongoDoctorRepository(client)
        patient_repo = MongoPatientRepository(client)
        appointment_repo = MongoAppointmentRepository(client)
        use_mongo = True
        print("[FindMyDOC] Connected to MongoDB repository backend.")
    except Exception as e:
        print(f"[FindMyDOC] Notice: MongoDB connection failed ({e}). Falling back to In-Memory repository.")
        use_mongo = False

if not use_mongo:
    user_repo = InMemoryUserRepository()
    doctor_repo = InMemoryDoctorRepository()
    patient_repo = InMemoryPatientRepository()
    appointment_repo = InMemoryAppointmentRepository()

__all__ = [
    "user_repo",
    "doctor_repo",
    "patient_repo",
    "appointment_repo",
    "get_datastore"
]

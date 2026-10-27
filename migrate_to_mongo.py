"""
FindMyDOC - Seed Data Migration to MongoDB
=========================================
Transfers seed data from data/seed.json to your MongoDB database.
Run this script anytime to seed or reset your MongoDB collections.

Usage:
  python migrate_to_mongo.py
"""

import os
import json
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/findmydoc")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "findmydoc")
SEED_PATH = os.path.join(os.path.dirname(__file__), "data", "seed.json")

def migrate():
    print(f"Connecting to MongoDB: {MONGO_URI} [Database: {DATABASE_NAME}]...")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        print("Connected to MongoDB successfully!")
    except Exception as e:
        print(f"Connection failed: {e}")
        print("\nEnsure MongoDB is running locally (e.g., mongod) or verify your Atlas MONGO_URI connection string.")
        return False

    db = client[DATABASE_NAME]

    if not os.path.exists(SEED_PATH):
        print(f"Seed file not found at {SEED_PATH}")
        return False

    with open(SEED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Users
    users = data.get("users", [])
    if users:
        db.users.delete_many({})
        for u in users:
            u["_id"] = u["id"]
        db.users.insert_many(users)
        print(f"Migrated {len(users)} users.")

    # 2. Doctors
    doctors = data.get("doctors", [])
    if doctors:
        db.doctors.delete_many({})
        for d in doctors:
            d["_id"] = d["id"]
        db.doctors.insert_many(doctors)
        print(f"Migrated {len(doctors)} doctors.")

    # 3. Patients
    patients = data.get("patients", [])
    if patients:
        db.patients.delete_many({})
        for p in patients:
            p["_id"] = p["id"]
        db.patients.insert_many(patients)
        print(f"Migrated {len(patients)} patients.")

    # 4. Appointments
    appointments = data.get("appointments", [])
    if appointments:
        db.appointments.delete_many({})
        for a in appointments:
            a["_id"] = a["id"]
        db.appointments.insert_many(appointments)
        print(f"Migrated {len(appointments)} appointments.")

    print("\nMongoDB migration complete! All collections are ready.")
    return True

if __name__ == "__main__":
    migrate()

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class BaseUserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def create(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass


class BaseDoctorRepository(ABC):
    @abstractmethod
    def get_by_id(self, doctor_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_all_cities(self) -> List[str]:
        pass

    @abstractmethod
    def get_all_specializations(self) -> List[str]:
        pass

    @abstractmethod
    def create(self, doctor_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update(self, doctor_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass


class BasePatientRepository(ABC):
    @abstractmethod
    def get_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def create(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update(self, patient_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass


class BaseAppointmentRepository(ABC):
    @abstractmethod
    def get_by_id(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_by_patient_id(self, patient_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_by_doctor_id(self, doctor_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def create(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_status(
        self,
        appointment_id: str,
        status: str,
        assigned_date: Optional[str] = None,
        assigned_time: Optional[str] = None,
        doctor_notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def cancel_by_patient(self, appointment_id: str, patient_id: str) -> bool:
        pass

    @abstractmethod
    def is_slot_booked(
        self,
        doctor_id: str,
        assigned_date: str,
        assigned_time: str,
        exclude_appointment_id: Optional[str] = None
    ) -> bool:
        pass

# agents/receptionist.py
from services.crew_api import query_huggingface

class ReceptionistAgent:
    """
    This agent acts like a hospital receptionist.
    It takes a patient's query (symptoms/issue) and decides
    which doctor they should visit.
    """

    def __init__(self):
        # We can define available doctors (rooms) here
        self.doctors = {
            "Dermatologist": ["skin", "rash", "itch", "allergy"],
            "Cardiologist": ["heart", "chest pain", "breath"],
            "Neurologist": ["headache", "seizure", "memory"],
            "Orthopedic": ["joint", "bone", "fracture"],
            "General Physician": ["fever", "cough", "weakness"],
        }

    def route_patient(self, query: str) -> str:
        """
        Uses Hugging Face LLM to map the patient's query
        to the best doctor.
        """
        # Craft a prompt for the LLM
        prompt = f"""
        You are a hospital receptionist.
        A patient comes with this issue: "{query}".

        Based on symptoms, decide the right doctor.
        Choose ONLY from this list: {", ".join(self.doctors.keys())}.
        Reply with ONLY the doctor's name.
        """

        # Call Hugging Face API (our wrapper from services/hf_api.py)
        response = query_huggingface(prompt)

        # In case model responds with extra words, clean it up
        doctor = response.split()[0]
        return doctor

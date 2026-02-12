from .doctor_base import DoctorAgent


class CardiologistAgent(DoctorAgent):
    def __init__(self):
        super().__init__(
            specialty="cardiologist",
            scope="Heart-related concerns: chest discomfort on exertion, palpitations, known heart disease follow-ups, blood pressure management advice (non-diagnostic).",
            red_flags=[
                "crushing chest pain", "chest pain radiating to jaw/arm", "shortness of breath at rest",
                "sweating and nausea with chest pain", "fainting", "very low blood pressure"
            ],
        )
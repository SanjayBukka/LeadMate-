from .doctor_base import DoctorAgent

class GeneralPhysicianAgent(DoctorAgent):
    def __init__(self):
        super().__init__(
            specialty="General Physician",
            scope="Common non-emergency issues: fever,cold/cough,sore throat,mild stomach issues,fatigue,general checkups.",
            red_flags=[
                "severe chest pain","difficulty breathing","confusion","fainting",
                "blue lips", "uncontrolled bleeding", "very high fever with stiff neck"
            ],
        )
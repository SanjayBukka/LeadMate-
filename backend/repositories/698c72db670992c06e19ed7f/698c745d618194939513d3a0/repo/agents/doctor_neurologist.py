from .doctor_base import DoctorAgent

class NeurologistAgent(DoctorAgent):
    def __init__(self):
        super().__init__(
            specialty="Neurologist",
            scope="Brain and nerves: persistent headaches, migraines, dizziness, seizures (history), numbness/tingling, memory concerns.",
            red_flags=[
                "sudden severe headache", "new weakness on one side", "speech difficulty",
                "seizure in someone without known epilepsy", "confusion with fever"
            ],
        )

from .doctor_base import DoctorAgent

class OrthopedicAgent(DoctorAgent):
    def __init__(self):
        super().__init__(
            specialty="Orthopedic",
            scope="Bones, joints, and muscles: sprains, strains, joint pain, back/neck pain, suspected minor fractures (non-emergency triage).",
            red_flags=[
                "open fracture", "severe deformity", "inability to bear weight with severe pain",
                "loss of limb sensation", "fever with hot swollen joint"
            ],
        )

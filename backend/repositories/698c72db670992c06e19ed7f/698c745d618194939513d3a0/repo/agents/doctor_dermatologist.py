from .doctor_base import DoctorAgent

class DermatologistAgent(DoctorAgent):
    def __init__(self):
        super().__init__(
            specialty="Dermatologist",
            scope="Skin, hair, and nail problems: rashes, acne, eczema, psoriasis, fungal infections, allergic dermatitis, dandruff.",
            red_flags=[
                "rash with high fever", "rapidly spreading redness", "blistering over large area",
                "facial swelling or throat tightness", "signs of severe infection"
            ],
        )

# agents/doctor_base.py
from typing import List, Dict
from services.crew_api import chat_hf

DISCLAIMER = (
    "IMPORTANT: I am a virtual assistant for educational purposes only. "
    "This is not a medical diagnosis. If symptoms are severe or worsening, "
    "seek in-person care or emergency services."
)

class DoctorAgent:
    """
    Base class for specialist doctor chat agents.
    Holds a conversation history and enforces safe, scoped replies.
    """

    def __init__(self, specialty: str, scope: str, red_flags: List[str]):
        self.specialty = specialty
        self.scope = scope
        self.red_flags = red_flags
        self.history: List[Dict[str, str]] = []  # [{"role": "user"/"assistant", "content": "..."}]

    def _system_prompt(self) -> str:
        return (
            f"You are a careful, empathetic {self.specialty}.\n"
            f"Scope: {self.scope}\n"
            "Rules:\n"
            "1) Start by asking 3–6 focused questions to clarify symptoms (duration, severity, triggers, relevant history, medications, allergies).\n"
            "2) Keep language simple and supportive. Avoid medical jargon unless explained.\n"
            "3) Do NOT give definitive diagnoses. Provide likely possibilities, self-care tips, and when to see a doctor.\n"
            "4) If the issue is outside your scope, say so and suggest a relevant specialist.\n"
            "5) If any RED FLAGS appear, advise immediate emergency care.\n"
            f"Common red flags to watch for: {', '.join(self.red_flags)}\n"
            f"Always include this disclaimer at the end of your message: {DISCLAIMER}\n"
        )

    def ask(self, user_message: str) -> str:
        """One chat turn: send user message + history to the model, return assistant reply, and store it."""
        messages = [{"role": "system", "content": self._system_prompt()}]
        messages.extend(self.history)  # previous turns
        messages.append({"role": "user", "content": user_message})

        reply = chat_hf(messages)
        # store turn
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": reply})
        return reply



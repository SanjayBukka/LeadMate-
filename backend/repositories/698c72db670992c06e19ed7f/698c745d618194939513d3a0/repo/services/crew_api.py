# services/crew_api.py
"""Crew AI service wrapper for the Virtual Hospital project.
This module provides both simple LLM access and a Crew (via the `crewai` SDK) 
that orchestrates the receptionist, triage, and specialist doctor agents.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Expect the Crew AI API key in the environment
CREW_API_KEY = os.getenv("CREW_API_KEY")
if not CREW_API_KEY:
    raise RuntimeError("CREW_API_KEY is missing in .env file")

# Set GROQ_API_KEY for litellm
os.environ["GROQ_API_KEY"] = CREW_API_KEY

# Define the LLM to be used
# Using a valid Groq model
MODEL_NAME = "groq/llama-3.3-70b-versatile"

# Import Crew AI SDK
from crewai import Crew, Agent, Task
from crewai.process import Process

def _simple_llm_call(prompt: str) -> str:
    """Helper for a single LLM completion call."""
    try:
        response = completion(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def _simple_chat_call(messages: list) -> str:
    """Helper for a chat-style LLM call."""
    try:
        response = completion(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# ---------------------------------------------------------------------------
# Public wrapper functions (keep original names for backward compatibility)
# ---------------------------------------------------------------------------

def query_huggingface(prompt: str) -> str:
    """Legacy wrapper – forwards a single prompt to the LLM.
    Used by the Receptionist for routing.
    """
    return _simple_llm_call(prompt)

def chat_hf(messages: list) -> str:
    """Legacy chat wrapper – formats a list of messages and runs the LLM.
    Used by the Doctor agents for conversation.
    """
    return _simple_chat_call(messages)

# ---------------------------------------------------------------------------
# Crew AI Workflow (Optional / Advanced)
# ---------------------------------------------------------------------------

def run_hospital_crew(patient_query: str) -> str:
    """Construct and run a Crew that coordinates the virtual hospital workflow.
    This can be used for a 'Full Consultation' feature.
    """
    
    # Receptionist agent
    receptionist = Agent(
        role="Receptionist",
        goal="Route the patient to the appropriate specialist",
        backstory="You work at a virtual hospital front desk. You are polite and efficient.",
        verbose=True,
        llm=MODEL_NAME
    )

    # Triage agent
    triage = Agent(
        role="Triage Specialist",
        goal="Identify the most relevant medical specialty and assess urgency",
        backstory="You are an experienced triage doctor who can quickly identify red flags.",
        verbose=True,
        llm=MODEL_NAME
    )

    # Specialist doctor agent
    doctor = Agent(
        role="Specialist Doctor",
        goal="Provide detailed medical advice and next steps",
        backstory="You are a highly skilled specialist with deep medical knowledge.",
        verbose=True,
        llm=MODEL_NAME
    )

    # Define tasks
    reception_task = Task(
        description=f"Given the patient query: '{patient_query}', decide which specialty to forward to.",
        expected_output="The name of the specialty (e.g., Cardiologist).",
        agent=receptionist,
    )
    
    triage_task = Task(
        description=f"Analyse the symptoms in '{patient_query}' and produce a concise recommendation.",
        expected_output="A short recommendation and any red-flag warnings.",
        agent=triage,
    )
    
    doctor_task = Task(
        description=f"Based on the triage report for '{patient_query}', provide a helpful, safe medical response with a disclaimer.",
        expected_output="A friendly, detailed answer with a medical disclaimer.",
        agent=doctor,
    )

    crew = Crew(
        agents=[receptionist, triage, doctor],
        tasks=[reception_task, triage_task, doctor_task],
        process=Process.sequential,
        verbose=True,
    )
    
    result = crew.kickoff()
    return result

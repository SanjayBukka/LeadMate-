import streamlit as st
import os
from agents.receptionist import ReceptionistAgent
from agents.doctor_dermatologist import DermatologistAgent
from agents.doctor_cardiologist import CardiologistAgent
from agents.doctor_neurologist import NeurologistAgent
from agents.doctor_orthopedic import OrthopedicAgent
from agents.doctor_general import GeneralPhysicianAgent
from services.crew_api import run_hospital_crew

# --- Page Config ---
st.set_page_config(page_title="Med-Agent-Orchestrator", page_icon="🏥", layout="wide")

# --- Load Custom CSS ---
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Initialize receptionist ---
reception = ReceptionistAgent()

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "doctor" not in st.session_state:
    st.session_state.doctor = None
if "full_consultation" not in st.session_state:
    st.session_state.full_consultation = None

# --- Header ---
st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1 style='font-size: 3rem; margin-bottom: 0;'>🏥 Med-Agent-Orchestrator</h1>
        <p style='font-size: 1.2rem; opacity: 0.8;'>Advanced Multi-Agent Clinical Triage System</p>
    </div>
""", unsafe_allow_html=True)

# --- Doctor Directory ---
doctor_directory = {
    "Dermatologist": {
        "agent": DermatologistAgent(),
        "specialty": "Skin, rashes, allergies",
        "avatar": "https://cdn-icons-png.flaticon.com/512/4320/4320371.png",
    },
    "Cardiologist": {
        "agent": CardiologistAgent(),
        "specialty": "Heart & chest pain",
        "avatar": "https://cdn-icons-png.flaticon.com/512/4320/4320368.png",
    },
    "Neurologist": {
        "agent": NeurologistAgent(),
        "specialty": "Brain & memory issues",
        "avatar": "https://cdn-icons-png.flaticon.com/512/4320/4320381.png",
    },
    "Orthopedic": {
        "agent": OrthopedicAgent(),
        "specialty": "Bones, joints, injuries",
        "avatar": "https://cdn-icons-png.flaticon.com/512/4320/4320365.png",
    },
    "General Physician": {
        "agent": GeneralPhysicianAgent(),
        "specialty": "Fever, cough, common issues",
        "avatar": "https://cdn-icons-png.flaticon.com/512/4320/4320379.png",
    },
}

# --- Sidebar ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2966/2966327.png", width=100)
    st.title("Hospital Info")
    st.info("Our AI doctors are available 24/7 for guidance. Please note this is not a substitute for professional medical advice.")
    
    if st.button("Reset Session", use_container_width=True):
        st.session_state.doctor = None
        st.session_state.messages = []
        st.session_state.full_consultation = None
        st.rerun()

# --- Step 1: Reception Desk ---
if st.session_state.doctor is None and st.session_state.full_consultation is None:
    st.image("https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&q=80&w=1000", use_container_width=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 👩‍💼 Reception Desk")
        st.markdown("Describe your symptoms below, and our Receptionist will guide you to the right doctor’s room.")

        query = st.text_area(
            "📝 Describe your issue:",
            placeholder="e.g., I have chest pain while running...",
            height=150
        )

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("🔍 Find My Doctor", use_container_width=True):
                if query.strip():
                    with st.spinner("Routing you to the best specialist..."):
                        doctor = reception.route_patient(query).strip().rstrip(".")
                        # Clean up response if it's more than one word
                        doctor = doctor.split()[0].replace(":", "").replace("*", "")
                        
                        # Try to match
                        matched = False
                        for d_name in doctor_directory.keys():
                            if d_name.lower() in doctor.lower():
                                st.session_state.doctor = d_name
                                matched = True
                                break
                        
                        if matched:
                            st.success(f"✅ Please proceed to the **{st.session_state.doctor}** room.")
                            st.rerun()
                        else:
                            st.error(f"❌ Sorry, we couldn't find a matching doctor for '{doctor}'. Please try again or select manually.")
                else:
                    st.warning("⚠️ Please enter your symptoms first.")
        
        with btn_col2:
            if st.button("🚀 Full AI Consultation (CrewAI)", use_container_width=True):
                if query.strip():
                    with st.spinner("Running full multi-agent consultation..."):
                        result = run_hospital_crew(query)
                        st.session_state.full_consultation = result
                        st.rerun()
                else:
                    st.warning("⚠️ Please enter your symptoms first.")

    with col2:
        st.markdown("### 🏥 Available Rooms")
        for doctor_name, info in doctor_directory.items():
            with st.container():
                st.markdown(f"""
                    <div class='doctor-card'>
                        <img src='{info['avatar']}' width='50' style='float: left; margin-right: 15px;'>
                        <div style='font-weight: 600;'>{doctor_name}</div>
                        <div style='font-size: 0.8rem; opacity: 0.7;'>{info['specialty']}</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"Enter {doctor_name} Room", key=f"btn_{doctor_name}"):
                    st.session_state.doctor = doctor_name
                    st.rerun()

# --- Step 2: Full Consultation Result ---
elif st.session_state.full_consultation:
    st.markdown("### 📋 Full Multi-Agent Consultation Report")
    st.markdown(st.session_state.full_consultation)
    
    if st.button("🔙 Back to Reception", use_container_width=True):
        st.session_state.full_consultation = None
        st.rerun()

# --- Step 3: Doctor Room ---
else:
    doctor_info = doctor_directory[st.session_state.doctor]
    doctor_agent = doctor_info["agent"]

    st.markdown(f"### 👨‍⚕️ {st.session_state.doctor} Room")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(doctor_info["avatar"], width=150)
        st.markdown(f"**Specialty:** {doctor_info['specialty']}")
        st.markdown("---")
        if st.button("🔙 Back to Reception", use_container_width=True):
            st.session_state.doctor = None
            st.session_state.messages = []
            st.rerun()

    with col2:
        st.markdown("#### 💬 Chat with Doctor")
        
        # Chat container
        chat_container = st.container(height=400)
        with chat_container:
            for sender, msg in st.session_state.messages:
                if sender == "You":
                    st.markdown(f"<div class='chat-message user-message'><b>🧑 You:</b><br>{msg}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='chat-message bot-message'><b>👨‍⚕️ {sender}:</b><br>{msg}</div>", unsafe_allow_html=True)

        # Input area
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input("Type your message...", placeholder="e.g., How long will the recovery take?")
            submit_button = st.form_submit_button("📤 Send", use_container_width=True)
            
            if submit_button and user_input.strip():
                st.session_state.messages.append(("You", user_input))
                with st.spinner(f"{st.session_state.doctor} is thinking..."):
                    reply = doctor_agent.ask(user_input)
                    st.session_state.messages.append((st.session_state.doctor, reply))
                st.rerun()

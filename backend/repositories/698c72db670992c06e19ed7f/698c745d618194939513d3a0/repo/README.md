# 🏥 Med-Agent-Orchestrator

An advanced, multi-agent clinical triage and guidance system designed for automated healthcare orchestration.

## 🌟 Features

- **👩‍💼 AI Receptionist**: Intelligently routes patients to the correct specialist based on symptoms.
- **👨‍⚕️ Specialist Doctors**: Dedicated agents for Cardiology, Dermatology, Neurology, Orthopedics, and General Medicine.
- **🚀 Full AI Consultation**: A comprehensive multi-agent workflow powered by **CrewAI** (Receptionist → Triage → Specialist).
- **💎 Premium UI**: A sleek, glassmorphism-inspired interface built with Streamlit and custom CSS.
- **⚡ Fast Backend**: Powered by **Groq** (Llama 3.3 70B) for near-instant responses.

## 🛠️ Tech Stack

- **Frontend**: Streamlit, Custom CSS
- **Orchestration**: CrewAI, LiteLLM
- **LLM**: Groq (Llama 3.3 70B)
- **Language**: Python

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- A Groq API Key

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/virtual-hospital-token.git
   cd virtual-hospital-token
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```env
   CREW_API_KEY=your_groq_api_key_here
   ```

### Running the App

```bash
streamlit run app.py
```

## ⚠️ Disclaimer

This application is for **educational purposes only**. It does not provide medical diagnoses. Always consult a professional healthcare provider for medical advice.

---
Built with ❤️ by Sanjay

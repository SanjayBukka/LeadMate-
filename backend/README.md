# LeadMate Backend

LeadMate is an AI-powered engineering assistant that helps teams analyze Git repositories, track developer contributions, and generate project health reports.

## Setup

1.  **Prerequisites**:
    *   Python 3.9+
    *   MongoDB
    *   Ollama (optional, for AI insights)

2.  **Installation**:
    ```bash
    cd backend
    pip install -r requirements.txt
    ```

3.  **Configuration**:
    *   Copy `.env.example` to `.env` and fill in the required values.
    *   `CORS_ORIGINS`: Comma-separated list of allowed origins.
    *   `MONGODB_URL`: Your MongoDB connection string.

4.  **Running the API**:
    ```bash
    python main.py
    ```

## Features

*   **Repository Analysis**: Clone and analyze Git repositories for commits, developer stats, and file types.
*   **AI Insights**: Generate project summaries and developer performance reports using Ollama.
*   **Team Management**: Track team members and their contributions.
*   **Document Q&A**: Ask questions about your project documents.

## Testing

Run tests using `pytest`:
```bash
pytest tests/
```

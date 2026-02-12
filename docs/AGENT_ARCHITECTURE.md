# Lead Mate - Agent Architecture Documentation

## Overview

Lead Mate uses a **Multi-Agent System** powered by **CrewAI** for intelligent project management. The system consists of specialized AI agents that collaborate to analyze documents, form teams, assign tasks, and provide insights.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LEAD MATE AGENT SYSTEM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐                         ┌─────────────────┐           │
│   │   FRONTEND      │   REST API / SSE        │    BACKEND      │           │
│   │   (React)       │ ◄──────────────────────►│   (FastAPI)     │           │
│   └─────────────────┘                         └────────┬────────┘           │
│                                                        │                    │
│   ┌────────────────────────────────────────────────────┴────────────────┐   │
│   │                        AGENT ORCHESTRATION LAYER                     │   │
│   │                                                                      │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │   │
│   │  │  DOCUMENT    │  │    STACK     │  │    TEAM      │  │   TASK   │ │   │
│   │  │    AGENT     │  │    AGENT     │  │    AGENT     │  │   AGENT  │ │   │
│   │  │              │  │              │  │              │  │          │ │   │
│   │  │ • Doc Q&A    │  │ • Tech Stack │  │ • Team Mgmt  │  │ • Tasks  │ │   │
│   │  │ • Analysis   │  │ • Resumes    │  │ • Dynamics   │  │ • Assign │ │   │
│   │  │ • Summary    │  │ • Formation  │  │ • Analysis   │  │ • Track  │ │   │
│   │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────┬─────┘ │   │
│   │         │                 │                 │               │       │   │
│   │         ▼                 ▼                 ▼               ▼       │   │
│   │  ┌────────────────────────────────────────────────────────────────┐ │   │
│   │  │                    TEAM FORMATION AGENT                        │ │   │
│   │  │              (CrewAI Multi-Agent Orchestration)                │ │   │
│   │  │                                                                │ │   │
│   │  │   ┌────────────┐  ┌────────────┐  ┌─────────────────┐         │ │   │
│   │  │   │   Team     │  │   Skills   │  │    Project      │         │ │   │
│   │  │   │  Analyst   │  │  Matcher   │  │  Coordinator    │         │ │   │
│   │  │   └────────────┘  └────────────┘  └─────────────────┘         │ │   │
│   │  └────────────────────────────────────────────────────────────────┘ │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                          DATA LAYER                                  │   │
│   │                                                                      │   │
│   │   ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐    │   │
│   │   │   ChromaDB   │   │   MongoDB    │   │       Ollama         │    │   │
│   │   │  (Vectors)   │   │   (Data)     │   │    (LLM Engine)      │    │   │
│   │   │              │   │              │   │                      │    │   │
│   │   │ • Documents  │   │ • Users      │   │ • llama3.2:3b        │    │   │
│   │   │ • Embeddings │   │ • Projects   │   │ • Chat completion    │    │   │
│   │   │ • Chat Hist  │   │ • Documents  │   │ • Streaming          │    │   │
│   │   │ • Iterations │   │ • Tasks      │   │                      │    │   │
│   │   └──────────────┘   └──────────────┘   └──────────────────────┘    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Details

### 1. Document Agent (`document_agent.py`)

**Purpose**: Analyzes project documentation and maintains conversational Q&A with the team lead.

**Role in CrewAI**:
```python
Agent(
    role='Project Documentation Analyst',
    goal='Analyze project documentation and help the lead understand requirements',
    backstory='Expert project analyst with experience in technical requirements...'
)
```

**Key Capabilities**:
| Feature | Description |
|---------|-------------|
| Document Upload | Processes PDF, DOCX, TXT files |
| Text Chunking | Splits documents into 1000-char chunks with 200-char overlap |
| Vector Search | ChromaDB semantic search for relevant context |
| Q&A Chat | Answers questions about uploaded documents |
| SSE Streaming | Real-time token streaming for responses |
| LLM Caching | Caches responses to avoid redundant LLM calls |

**Data Flow**:
```
User uploads document
       ↓
Extract text (PDF/DOCX/TXT)
       ↓
Split into chunks (RecursiveCharacterTextSplitter)
       ↓
Store in ChromaDB (with embeddings)
       ↓
User asks question
       ↓
Search relevant chunks (vector similarity)
       ↓
Generate response (Ollama LLM)
       ↓
Stream response via SSE
```

**ChromaDB Collections**:
- `documents` - Uploaded document chunks
- `doc_chat` - Conversation history

---

### 2. Stack Agent (`stack_agent.py`)

**Purpose**: Forms teams based on document analysis and resume processing.

**Role in CrewAI**:
```python
Agent(
    role='Senior Team Formation Specialist',
    goal='Form optimal teams based on project requirements and team member skills',
    backstory='Expert in team formation with 15+ years experience...'
)
```

**Key Capabilities**:
| Feature | Description |
|---------|-------------|
| Resume Processing | Extracts skills from PDF resumes |
| Skills Extraction | Uses LLM to identify programming languages, frameworks, etc. |
| Team Generation | Creates initial team recommendation |
| Iterative Refinement | Adjusts team based on lead feedback |
| Final Report | Generates comprehensive team formation report |

**Iteration Workflow**:
```
1. Lead uploads resumes
          ↓
2. Stack Agent extracts skills from each resume
          ↓
3. Document Agent context is retrieved (requirements)
          ↓
4. Initial team is generated with reasoning
          ↓
5. Lead provides feedback ("Replace X with Y")
          ↓
6. Stack Agent iterates on team composition
          ↓
7. Process repeats until lead approves
          ↓
8. Final comprehensive report generated
```

**ChromaDB Collections**:
- `resumes` - Uploaded team member resumes
- `stack_iterations` - Team formation iteration history

---

### 3. Team Agent (`team_agent.py`)

**Purpose**: Manages team members, roles, and team dynamics.

**Role in CrewAI**:
```python
Agent(
    role='Team Management Expert',
    goal='Help with team building, role assignments, and optimization',
    backstory='Expert team manager with extensive experience...'
)
```

**Key Capabilities**:
| Feature | Description |
|---------|-------------|
| Team Management | CRUD operations on team members |
| Role Assignment | Suggests optimal role assignments |
| Dynamics Analysis | Analyzes team collaboration patterns |
| Performance Metrics | Tracks team KPIs |

**ChromaDB Collections**:
- `team_members` - Team member data and roles
- `team_chat` - Conversation history

---

### 4. Task Agent (`task_agent.py`)

**Purpose**: Generates actionable project tasks from requirements and team formation.

**Role in CrewAI**:
```python
Agent(
    role='Task Generation Specialist',
    goal='Generate actionable tasks with assignments and priorities',
    backstory='Expert in project planning and task breakdown...'
)
```

**Key Capabilities**:
| Feature | Description |
|---------|-------------|
| Task Generation | Creates tasks from requirements |
| Assignment | Assigns tasks to team members |
| Priority Setting | Sets task priorities (High/Medium/Low) |
| Timeline Estimation | Estimates task duration |
| Dependencies | Links related tasks |

**Integration Points**:
```
Document Agent (requirements)
        ↓
Stack Agent (team formation)
        ↓
Task Agent generates tasks
        ↓
Tasks assigned to team members
```

---

### 5. Team Formation Agent (`team_formation_agent.py`)

**Purpose**: Advanced orchestration agent that coordinates all other agents using CrewAI.

**Multi-Agent Crew Structure**:
```python
# Team Analyst Agent
Agent(
    role="Team Analyst",
    goal="Analyze team composition, skills, and dynamics"
)

# Skills Matcher Agent
Agent(
    role="Skills Matcher", 
    goal="Match team member skills with project requirements"
)

# Project Coordinator Agent
Agent(
    role="Project Coordinator",
    goal="Coordinate team formation with project timeline"
)
```

**CrewAI Orchestration Flow**:
```
┌─────────────────────────────────────────────────────────────┐
│                   CREW EXECUTION FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   INPUT: Project requirements + Available team members       │
│                          ↓                                   │
│   ┌──────────────────────────────────────────────────────┐  │
│   │  TASK 1: Team Analysis (Team Analyst Agent)          │  │
│   │  • Analyze team composition                           │  │
│   │  • Evaluate skill gaps                                │  │
│   │  • Recommend team structure                           │  │
│   └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│   ┌──────────────────────────────────────────────────────┐  │
│   │  TASK 2: Skills Matching (Skills Matcher Agent)      │  │
│   │  • Map skills to requirements                         │  │
│   │  • Identify missing skills                            │  │
│   │  • Recommend training                                 │  │
│   └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│   ┌──────────────────────────────────────────────────────┐  │
│   │  TASK 3: Coordination (Project Coordinator Agent)    │  │
│   │  • Align with timeline                                │  │
│   │  • Resource allocation                                │  │
│   │  • Risk mitigation                                    │  │
│   └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│   OUTPUT: Comprehensive team formation recommendations       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Agent Connections & Data Sharing

### Inter-Agent Communication

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AGENT CONNECTION MAP                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   DOCUMENT AGENT ─────────────────────► STACK AGENT                     │
│   • Project requirements                • Uses document context         │
│   • Technical specifications            • Requirements clarification     │
│   • Chat history (Q&A)                  • Informed team formation        │
│                                                                          │
│   DOCUMENT AGENT ─────────────────────► TEAM AGENT                      │
│   • Project documents                   • Project understanding          │
│   • Requirements analysis               • Role requirements              │
│                                                                          │
│   DOCUMENT AGENT ─────────────────────► TASK AGENT                      │
│   • Requirements breakdown              • Task generation input          │
│   • Technical specs                     • Priority indicators            │
│                                                                          │
│   STACK AGENT ────────────────────────► TASK AGENT                      │
│   • Final team composition              • Task assignment targets        │
│   • Skill profiles                      • Workload distribution          │
│                                                                          │
│   ALL AGENTS ─────────────────────────► TEAM FORMATION AGENT            │
│   • Document context                    • Comprehensive analysis         │
│   • Tech stack context                  • Multi-perspective decisions    │
│   • Chat history                        • Coordinated output             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Shared Data via ChromaDB

All agents share the same ChromaDB directory structure:
```
chroma_db/
├── company_{company_id}/
│   └── lead_{lead_id}/
│       ├── documents/          ← Document Agent writes
│       ├── doc_chat/           ← Document Agent writes
│       ├── resumes/            ← Stack Agent writes
│       ├── stack_iterations/   ← Stack Agent writes
│       ├── team_members/       ← Team Agent writes
│       ├── team_chat/          ← Team Agent writes
│       ├── tasks/              ← Task Agent writes
│       └── final_reports/      ← Stack Agent writes
```

---

## LLM Configuration

### Primary LLM: Ollama (Local)

```python
# Default configuration
ollama_model = "llama3.2:3b"
ollama_base_url = "http://localhost:11434"

# CrewAI integration
crewai_llm = f"ollama/{ollama_model}"
```

### Fallback: Google Gemini (Cloud)

```python
# Only used if explicitly enabled
USE_GEMINI = "true"
GOOGLE_API_KEY = "your-api-key"
```

### LLM Priority Flow:
```
1. Check FORCE_OLLAMA env var → Use Ollama
2. Check USE_GEMINI + GOOGLE_API_KEY → Try Gemini
3. Gemini fails? → Fallback to Ollama
4. All fail? → Use fallback responses (no LLM)
```

---

## API Endpoints

### Document Agent Routes (`/api/agents/doc-agent/`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Non-streaming chat |
| `/chat/stream` | POST | SSE streaming chat |
| `/summary` | POST | Generate project summary |
| `/history/{project_id}` | GET | Get chat history |
| `/cache/stats` | GET | Get LLM cache stats |
| `/cache/clear` | POST | Clear LLM cache |

### Team Formation Routes (`/api/team-formation/`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Chat with formation agent |
| `/analyze` | POST | Analyze team formation |
| `/context` | GET | Get agent context |

### Task Routes (`/api/tasks/`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/generate` | POST | Generate tasks from requirements |
| `/list` | GET | List all tasks |
| `/update` | PUT | Update task status |

---

## SSE Streaming Implementation

### Backend (Python/FastAPI)
```python
async def answer_question_stream(self, question: str) -> AsyncGenerator[str, None]:
    # Check cache first
    cached = llm_cache.get(prompt=question)
    if cached:
        # Stream cached response word by word
        for word in cached.split():
            yield f"data: {json.dumps(word)}\n\n"
            await asyncio.sleep(0.02)
        yield "data: [DONE]\n\n"
        return
    
    # Stream from Ollama
    stream = ollama.chat(model='llama3.2:3b', messages=[...], stream=True)
    for chunk in stream:
        token = chunk['message']['content']
        yield f"data: {json.dumps(token)}\n\n"
    
    # Cache complete response
    llm_cache.set(prompt=question, response=full_response)
    yield "data: [DONE]\n\n"
```

### Frontend (React/TypeScript)
```typescript
const reader = response.body?.getReader();
while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const token = JSON.parse(line.substring(6));
            // Update UI with token
            setContent(prev => prev + token);
        }
    }
}
```

---

## LLM Response Caching

### Cache Service (`cache_service.py`)
```python
class CacheService:
    def __init__(self, ttl_seconds: int = 3600):  # 1 hour default
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
    
    def _generate_key(self, prompt: str, context: str, model: str) -> str:
        combined = f"{prompt}|{context}|{model}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get(self, prompt: str, ...) -> Optional[str]:
        key = self._generate_key(prompt, context, model)
        if key in self._cache and not expired:
            self.hits += 1
            return self._cache[key]['response']
        self.misses += 1
        return None
```

### Cache Statistics
```json
{
    "total_cached": 5,
    "hits": 12,
    "misses": 3,
    "hit_rate": "80.00%",
    "ttl_seconds": 3600
}
```

---

## Environment Variables

```bash
# LLM Configuration
FORCE_OLLAMA=true              # Force Ollama even if Gemini is available
USE_GEMINI=false               # Enable Gemini API
GOOGLE_API_KEY=                # Gemini API key
OLLAMA_MODEL=llama3.2:3b       # Ollama model name
OLLAMA_BASE_URL=http://localhost:11434

# Database
MONGODB_URI=mongodb+srv://...  # MongoDB connection string

# Security
JWT_SECRET=your-secret-key     # JWT signing key
```

---

## CrewAI Process Types

### Sequential Process (Default)
```python
crew = Crew(
    agents=[agent1, agent2, agent3],
    tasks=[task1, task2, task3],
    process=Process.sequential  # Tasks run one after another
)
```

### Hierarchical Process (Advanced)
```python
crew = Crew(
    agents=[manager, worker1, worker2],
    tasks=[complex_task],
    process=Process.hierarchical,  # Manager delegates to workers
    manager_llm=manager_llm
)
```

---

## Summary

Lead Mate's agent system provides:

1. **Specialized Agents** - Each agent has a focused role
2. **CrewAI Orchestration** - Multi-agent collaboration
3. **Shared Context** - ChromaDB enables inter-agent data sharing
4. **Iterative Workflows** - Support for feedback loops
5. **Real-time Streaming** - SSE for live responses
6. **Intelligent Caching** - Avoid redundant LLM calls
7. **Local-First LLM** - Ollama for privacy and speed

The system enables intelligent project management by combining document analysis, team formation, and task generation into a cohesive, AI-powered workflow.

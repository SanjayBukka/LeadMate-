# Mermaid Flowcharts for LeadMate Project

## 1. High-Level System Architecture

```mermaid
graph TB
    A[User Interface<br/>React + TypeScript] --> B[API Layer<br/>FastAPI]
    B --> C[AI Agents<br/>CrewAI + LLMs]
    B --> D[MongoDB<br/>Structured Data]
    B --> E[ChromaDB<br/>Vector Embeddings]
    C --> D
    C --> E
    F[Ollama<br/>Llama3.2:3b] --> C
    G[Google Gemini<br/>Fallback] --> C
```

## 2. Multi-Agent System Architecture

```mermaid
graph TB
    A[Project Data] --> B[Document Agent]
    A --> C[Stack Agent]
    A --> D[Team Formation Agent]
    A --> E[Task Agent]
    B --> C
    B --> D
    B --> E
    C --> D
    D --> E
    B --> F[MongoDB]
    C --> F
    D --> F
    E --> F
    B --> G[ChromaDB]
    C --> G
    D --> G
    E --> G
```

## 3. Project-Centric Data Flow

```mermaid
graph TB
    A[Project Scope<br/>Project ID: XYZ] --> B[Documents]
    A --> C[Resumes]
    A --> D[Tasks]
    B --> E[MongoDB<br/>Documents]
    C --> F[MongoDB<br/>Team Members]
    D --> G[MongoDB<br/>Tasks]
    B --> H[ChromaDB<br/>Documents]
    C --> I[ChromaDB<br/>Resumes]
```

## 4. Agent Interaction Workflow

```mermaid
graph TB
    A[Project Creation] --> B[Document Agent<br/>Analyzes Requirements]
    B --> C[Stack Agent<br/>Recommends Tech Stack]
    C --> D[Team Formation Agent<br/>Forms Team]
    D --> E[Task Agent<br/>Generates Tasks]
    E --> F[Project Execution]
```

## 5. User Interaction Flow

```mermaid
graph TB
    A[Project Manager] --> B[Create Project]
    B --> C[Assign Team Lead]
    C --> D[Upload Documents]
    D --> E[Web Application<br/>React + TypeScript]
    
    F[Team Lead] --> G[Chat with Document Agent]
    G --> H[Upload Resumes]
    H --> I[Get Stack Recommendation]
    I --> J[Form Team]
    J --> K[Generate Tasks]
    K --> E
    
    E --> L[API Layer<br/>FastAPI]
    L --> M[AI Agents]
    M --> N[Database]
    N --> M
    M --> L
    L --> E
```

## 6. Comprehensive System Architecture - User Perspective

```mermaid
graph TB
    A[Project Manager] --> B[1. Create Project]
    B --> C[2. Assign Team Lead]
    C --> D[3. Upload Documents]
    D --> E[Document Agent<br/>Llama3.2:3b]
    
    F[Team Lead] --> G[4. Chat with Document Agent]
    G --> H[5. Upload Resumes]
    H --> I[6. Get Stack Recommendation]
    I --> J[7. Form Team]
    J --> K[8. Generate Tasks]
    
    E --> L[Document Analysis<br/>5-10s]
    I --> M[Tech Stack<br/>7-12s]
    J --> N[Team Formation<br/>10-15s]
    K --> O[Task List<br/>12-18s]
    
    E --> P[Model Limitations<br/>65-70% Accuracy<br/>5-15s Response Time]
    M --> P
    N --> P
    O --> P
```

## 7. Technical Data Flow Architecture

```mermaid
graph TB
    A[Presentation Layer<br/>Web UI] --> B[Application Layer<br/>API Services]
    B --> C[Business Logic Layer<br/>AI Agents]
    C --> D[Data Layer<br/>Databases]
    D --> E[External Services<br/>LLM Providers]
    
    B --> F[Authentication]
    B --> G[Project Service]
    B --> H[Document Service]
    
    C --> I[Document Agent]
    C --> J[Stack Agent]
    C --> K[Team Agent]
    C --> L[Task Agent]
    
    D --> M[MongoDB]
    D --> N[ChromaDB]
    
    E --> O[Ollama<br/>Llama3.2:3b]
    E --> P[Google Gemini<br/>Fallback]
    
    H --> I
    I --> M
    I --> N
    I --> O
```

## 8. Document Agent Workflow

```mermaid
graph TB
    A[Document Upload] --> B[Text Extraction]
    B --> C[Text Chunking]
    C --> D[Vector Embedding]
    D --> E[Store in ChromaDB]
    E --> F[Chat Interface]
    F --> G[Response Generation]
    G --> A
```

## 9. Stack Agent Workflow

```mermaid
graph TB
    A[Project Requirements] --> B[Initial Recommendation]
    B --> C[Team Lead Feedback]
    C --> D[Refine Recommendation]
    D --> E[Iteration Check]
    E -->|No| C
    E -->|Yes| F[Final Report]
```

## 10. Team Formation Algorithm Workflow

```mermaid
graph TB
    A[Resume Upload] --> B[Skill Extraction]
    B --> C[Skill Matching]
    C --> D[Team Optimization]
    D --> E[Team Recommendation]
    E --> F[Skill Gap Analysis]
    F --> G[Final Team]
```

## 11. Task Generation Process

```mermaid
graph TB
    A[Project Requirements] --> B[Tech Stack]
    B --> C[Team Composition]
    C --> D[Task Breakdown]
    D --> E[Task Assignment]
    E --> F[Prioritization]
    F --> G[Task List]
```

## 12. Performance Visualization

```mermaid
pie
    title System Performance Metrics
    "Response Time" : 75
    "Accuracy" : 67
    "Usability" : 80
    "Satisfaction" : 78
```

## 13. Future Architecture Evolution

```mermaid
graph TB
    A[Current<br/>Architecture] --> B[ML Models]
    B --> C[Advanced NLP]
    C --> D[Tool Integration]
    D --> E[Mobile Apps]
    E --> F[Analytics]
    F --> A
```

## 14. System Limitations

```mermaid
graph LR
    A[Llama3.2:3b Model<br/>8GB RAM Limitations] --> B[Response Time<br/>5-15 seconds]
    A --> C[Accuracy<br/>65-70%]
    A --> D[Concurrent Users<br/>25 max]
    A --> E[Context Window<br/>8K tokens]
```

## 15. Comparison with Traditional Tools

```mermaid
graph LR
    A[Traditional Tools] --> B[Manual Team Formation<br/>Manual Tech Stack<br/>Manual Task Creation]
    C[LeadMate<br/>Llama3.2:3b] --> D[AI-Assisted Team Formation<br/>AI-Generated Tech Stack<br/>AI-Generated Tasks]
```
# Updated Mermaid Flowcharts for LeadMate Project with CodeClarity Agent

## 1. High-Level System Architecture with CodeClarity Agent

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
    H[Git Repository<br/>Code Analysis] --> I[CodeClarity Agent]
    I --> C
```

## 2. Multi-Agent System Architecture with CodeClarity Agent

```mermaid
graph TB
    A[Project Data] --> B[Document Agent]
    A --> C[Stack Agent]
    A --> D[Team Formation Agent]
    A --> E[Task Agent]
    A --> J[CodeClarity Agent]
    B --> C
    B --> D
    B --> E
    B --> J
    C --> D
    D --> E
    J --> B
    J --> C
    J --> D
    B --> F[MongoDB]
    C --> F
    D --> F
    E --> F
    J --> F
    B --> G[ChromaDB]
    C --> G
    D --> G
    E --> G
    J --> G
```

## 3. Project-Centric Data Flow with CodeClarity Integration

```mermaid
graph TB
    A[Project Scope<br/>Project ID: XYZ] --> B[Documents]
    A --> C[Resumes]
    A --> D[Tasks]
    A --> K[Repository]
    B --> E[MongoDB<br/>Documents]
    C --> F[MongoDB<br/>Team Members]
    D --> G[MongoDB<br/>Tasks]
    K --> L[MongoDB<br/>Repo Analysis]
    B --> H[ChromaDB<br/>Documents]
    C --> I[ChromaDB<br/>Resumes]
    K --> M[ChromaDB<br/>Code Insights]
```

## 4. Agent Interaction Workflow with CodeClarity

```mermaid
graph TB
    A[Project Creation] --> B[Document Agent<br/>Analyzes Requirements]
    B --> N[CodeClarity Agent<br/>Analyzes Repository]
    N --> C[Stack Agent<br/>Recommends Tech Stack]
    C --> D[Team Formation Agent<br/>Forms Team]
    D --> E[Task Agent<br/>Generates Tasks]
    E --> F[Project Execution]
```

## 5. User Interaction Flow with CodeClarity

```mermaid
graph TB
    A[Project Manager] --> B[Create Project]
    B --> C[Assign Team Lead]
    C --> D[Upload Documents]
    D --> P[Link Git Repository]
    P --> E[Web Application<br/>React + TypeScript]
    
    F[Team Lead] --> G[Chat with Document Agent]
    G --> Q[Analyze Repository with<br/>CodeClarity Agent]
    Q --> H[Upload Resumes]
    H --> I[Get Stack Recommendation]
    I --> J[Form Team]
    J --> K[Generate Tasks]
    K --> E
    
    E --> L[API Layer<br/>FastAPI]
    L --> M[AI Agents]
    M --> R[Database]
    R --> M
    M --> L
    L --> E
```

## 6. Comprehensive System Architecture - User Perspective with CodeClarity

```mermaid
graph TB
    A[Project Manager] --> B[1. Create Project]
    B --> C[2. Assign Team Lead]
    C --> D[3. Upload Documents]
    D --> S[4. Link Repository]
    S --> E[Document Agent<br/>Llama3.2:3b]
    
    F[Team Lead] --> G[5. Chat with Document Agent]
    G --> T[6. Analyze Code with<br/>CodeClarity Agent]
    T --> H[7. Upload Resumes]
    H --> I[8. Get Stack Recommendation]
    I --> J[9. Form Team]
    J --> K[10. Generate Tasks]
    
    E --> U[Document Analysis<br/>5-10s]
    T --> V[Code Analysis<br/>8-15s]
    I --> W[Tech Stack<br/>7-12s]
    J --> X[Team Formation<br/>10-15s]
    K --> Y[Task List<br/>12-18s]
    
    E --> Z[Model Limitations<br/>65-70% Accuracy<br/>5-15s Response Time]
    V --> Z
    W --> Z
    X --> Z
    Y --> Z
```

## 7. Technical Data Flow Architecture with CodeClarity

```mermaid
graph TB
    A[Presentation Layer<br/>Web UI] --> B[Application Layer<br/>API Services]
    B --> C[Business Logic Layer<br/>AI Agents]
    C --> D[Data Layer<br/>Databases]
    D --> E[External Services<br/>LLM Providers]
    
    B --> F[Authentication]
    B --> G[Project Service]
    B --> H[Document Service]
    B --> I[Repository Service]
    
    C --> J[Document Agent]
    C --> K[Stack Agent]
    C --> L[Team Agent]
    C --> M[Task Agent]
    C --> N[CodeClarity Agent]
    
    D --> O[MongoDB]
    D --> P[ChromaDB]
    
    E --> Q[Ollama<br/>Llama3.2:3b]
    E --> R[Google Gemini<br/>Fallback]
    
    H --> J
    I --> N
    J --> O
    J --> P
    J --> Q
    K --> O
    K --> P
    K --> Q
    L --> O
    L --> P
    L --> Q
    M --> O
    M --> P
    M --> Q
    N --> O
    N --> P
    N --> Q
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

## 12. CodeClarity Agent Workflow

```mermaid
graph TB
    A[Repository Analysis Request] --> B[Clone Repository]
    B --> C[Extract Commit Data]
    C --> D[Analyze File Types]
    D --> E[Calculate Developer Stats]
    E --> F[Generate Code Insights]
    F --> G[Store Analysis Results]
    G --> H[Provide Clarity Recommendations]
    H --> I[AI Chat Interface]
    I --> A
```

## 13. CodeClarity Agent Integration with Other Agents

```mermaid
graph TB
    A[CodeClarity Agent] --> B[Document Agent]
    A --> C[Stack Agent]
    A --> D[Team Formation Agent]
    A --> E[Task Agent]
    B --> F[Enhanced<br/>Requirements]
    C --> G[Informed<br/>Tech Stack]
    D --> H[Optimized<br/>Team Formation]
    E --> I[Intelligent<br/>Task Generation]
```

## 14. Performance Visualization

```mermaid
pie
    title System Performance Metrics
    "Response Time" : 75
    "Accuracy" : 67
    "Usability" : 80
    "Satisfaction" : 78
```

## 15. Future Architecture Evolution with CodeClarity

```mermaid
graph TB
    A[Current<br/>Architecture] --> B[ML Models]
    B --> C[Advanced NLP]
    C --> D[Tool Integration]
    D --> J[CodeClarity<br/>Enhancements]
    J --> E[Mobile Apps]
    E --> F[Analytics]
    F --> A
```

## 16. System Limitations with CodeClarity

```mermaid
graph LR
    A[Llama3.2:3b Model<br/>8GB RAM Limitations] --> B[Response Time<br/>5-15 seconds]
    A --> C[Accuracy<br/>65-70%]
    A --> D[Concurrent Users<br/>25 max]
    A --> E[Context Window<br/>8K tokens]
    A --> F[Code Analysis<br/>Limited Depth]
```

## 17. Comparison with Traditional Tools Including CodeClarity

```mermaid
graph LR
    A[Traditional Tools] --> B[Manual Team Formation<br/>Manual Tech Stack<br/>Manual Task Creation<br/>No Code Analysis]
    G[LeadMate<br/>Llama3.2:3b] --> H[AI-Assisted Team Formation<br/>AI-Generated Tech Stack<br/>AI-Generated Tasks<br/>AI Code Analysis]
```
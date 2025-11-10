# Snowflake Cortex GenAI Pipeline - Flow Diagram

## High-Level Architecture Flow

```mermaid
graph TB
    %% Input Sources
    PDF[PDF Files] --> INGEST[Document Ingestion]
    DOCX[DOCX Files] --> INGEST
    TXT[Text Files] --> INGEST
    MD[Markdown Files] --> INGEST
    
    %% Ingestion Pipeline
    INGEST --> EXTRACT[Text Extraction]
    EXTRACT --> CHUNK[Text Chunking]
    CHUNK --> VALIDATE[Content Validation]
    VALIDATE --> STORE_RAW[(Raw Documents Table)]
    
    %% Embedding Pipeline
    STORE_RAW --> EMBED_GEN[Embedding Generation]
    EMBED_GEN --> CORTEX_EMBED[CORTEX.EMBED_TEXT_768]
    CORTEX_EMBED --> STORE_VEC[(Vector Embeddings Table)]
    
    %% Query Pipeline
    USER_Q[User Query] --> QUERY_EMBED[Query Embedding]
    QUERY_EMBED --> CORTEX_EMBED
    CORTEX_EMBED --> SEARCH[Vector Similarity Search]
    
    SEARCH --> STORE_VEC
    STORE_VEC --> SIMILAR[Top-K Similar Chunks]
    SIMILAR --> CONTEXT[Build Context]
    
    %% LLM Pipeline
    CONTEXT --> PROMPT[Enhanced Prompt]
    USER_Q --> PROMPT
    PROMPT --> LLM[CORTEX.COMPLETE]
    LLM --> RESPONSE[Generated Response]
    
    %% Monitoring & Storage
    EMBED_GEN --> TELEMETRY[(Telemetry Table)]
    SEARCH --> TELEMETRY
    LLM --> TELEMETRY
    RESPONSE --> QUERY_HIST[(Query History Table)]
    TELEMETRY --> DASHBOARD[Streamlit Dashboard]
    
    %% Styling
    classDef input fill:#e1f5fe
    classDef process fill:#f3e5f5
    classDef storage fill:#e8f5e8
    classDef cortex fill:#fff3e0
    classDef output fill:#fce4ec
    
    class PDF,DOCX,TXT,MD,USER_Q input
    class INGEST,EXTRACT,CHUNK,VALIDATE,EMBED_GEN,QUERY_EMBED,SEARCH,CONTEXT,PROMPT process
    class STORE_RAW,STORE_VEC,TELEMETRY,QUERY_HIST storage
    class CORTEX_EMBED,LLM cortex
    class SIMILAR,RESPONSE,DASHBOARD output
```

## Detailed Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant API as Query API
    participant EMB as Embedding Service
    participant VS as Vector Search
    participant LLM as LLM Service
    participant TEL as Telemetry
    participant DB as Snowflake DB
    
    Note over U,DB: Document Ingestion Phase
    U->>API: Upload Document
    API->>DB: Store Raw Document
    API->>EMB: Generate Embeddings
    EMB->>DB: CORTEX.EMBED_TEXT_768()
    DB->>EMB: Return Vector
    EMB->>DB: Store Embeddings
    EMB->>TEL: Log Metrics
    
    Note over U,DB: Query Processing Phase
    U->>API: Submit Query
    API->>EMB: Generate Query Embedding
    EMB->>DB: CORTEX.EMBED_TEXT_768()
    DB->>EMB: Return Query Vector
    
    API->>VS: Perform Similarity Search
    VS->>DB: VECTOR_COSINE_SIMILARITY()
    DB->>VS: Return Top-K Results
    VS->>TEL: Log Search Metrics
    
    API->>LLM: Enhanced Prompt + Context
    LLM->>DB: CORTEX.COMPLETE()
    DB->>LLM: Return Response
    LLM->>TEL: Log LLM Metrics
    
    API->>DB: Store Query History
    API->>U: Return Response + Metadata
    
    Note over TEL,DB: Continuous Monitoring
    TEL->>DB: Aggregate Metrics
    DB->>TEL: Performance Data
```

## Component Interaction Flow

```mermaid
graph LR
    subgraph "Input Layer"
        DOC[Documents]
        QUERY[User Queries]
    end
    
    subgraph "Processing Layer"
        INGEST[ingest_loader.py]
        EMBED[embed_generator.py]
        CORTEX_Q[cortex_query.py]
    end
    
    subgraph "Snowflake Cortex"
        CORTEX_EMB[CORTEX.EMBED_TEXT_768]
        CORTEX_LLM[CORTEX.COMPLETE]
        VECTOR_SEARCH[VECTOR_COSINE_SIMILARITY]
    end
    
    subgraph "Storage Layer"
        RAW_TBL[(media_raw)]
        EMB_TBL[(media_embeddings)]
        TEL_TBL[(genai_telemetry)]
        HIST_TBL[(query_history)]
    end
    
    subgraph "Monitoring Layer"
        TELEMETRY[telemetry_task.py]
        DASHBOARD[dashboard_plot.py]
    end
    
    subgraph "Management Layer"
        UTILS[utils.py]
        CONFIG[config/]
        CICD[pipelines/deploy.yaml]
    end
    
    %% Connections
    DOC --> INGEST
    INGEST --> RAW_TBL
    RAW_TBL --> EMBED
    EMBED --> CORTEX_EMB
    CORTEX_EMB --> EMB_TBL
    
    QUERY --> CORTEX_Q
    CORTEX_Q --> CORTEX_EMB
    CORTEX_Q --> VECTOR_SEARCH
    VECTOR_SEARCH --> EMB_TBL
    EMB_TBL --> CORTEX_Q
    CORTEX_Q --> CORTEX_LLM
    CORTEX_LLM --> CORTEX_Q
    
    CORTEX_Q --> HIST_TBL
    INGEST --> TELEMETRY
    EMBED --> TELEMETRY
    CORTEX_Q --> TELEMETRY
    TELEMETRY --> TEL_TBL
    TEL_TBL --> DASHBOARD
    
    UTILS --> INGEST
    UTILS --> EMBED
    UTILS --> CORTEX_Q
    UTILS --> TELEMETRY
    CONFIG --> UTILS
    CICD --> CONFIG
```

## Telemetry Data Flow

```mermaid
flowchart TD
    subgraph "Operations"
        OP1[Document Ingestion]
        OP2[Embedding Generation]
        OP3[Semantic Search]
        OP4[LLM Completion]
    end
    
    subgraph "Telemetry Collection"
        TRACKER[TelemetryTracker]
        BUFFER[Batch Buffer]
    end
    
    subgraph "Storage & Analysis"
        TEL_DB[(genai_telemetry)]
        METRICS[Performance Metrics]
        COSTS[Cost Analysis]
        ERRORS[Error Analysis]
    end
    
    subgraph "Visualization"
        DASH_PERF[Performance Charts]
        DASH_COST[Cost Breakdown]
        DASH_ERROR[Error Dashboard]
        ALERTS[Real-time Alerts]
    end
    
    OP1 --> TRACKER
    OP2 --> TRACKER
    OP3 --> TRACKER
    OP4 --> TRACKER
    
    TRACKER --> BUFFER
    BUFFER --> TEL_DB
    
    TEL_DB --> METRICS
    TEL_DB --> COSTS
    TEL_DB --> ERRORS
    
    METRICS --> DASH_PERF
    COSTS --> DASH_COST
    ERRORS --> DASH_ERROR
    ERRORS --> ALERTS
    
    DASH_PERF --> DASHBOARD_UI[Streamlit Dashboard]
    DASH_COST --> DASHBOARD_UI
    DASH_ERROR --> DASHBOARD_UI
    ALERTS --> DASHBOARD_UI
```

## CI/CD Pipeline Flow

```mermaid
graph TD
    PUSH[Git Push] --> VALIDATE[Code Validation]
    VALIDATE --> LINT[Linting & Testing]
    LINT --> SQL_CHECK[SQL Validation]
    
    SQL_CHECK --> DEPLOY_INFRA[Deploy Infrastructure]
    DEPLOY_INFRA --> SEED_DATA[Seed Sample Data]
    SEED_DATA --> PERF_TEST[Performance Testing]
    
    PERF_TEST --> HEALTH_CHECK[Health Checks]
    HEALTH_CHECK --> NOTIFY[Deployment Notification]
    
    subgraph "Validation Steps"
        VALIDATE --> BLACK[Black Formatting]
        VALIDATE --> FLAKE8[Flake8 Linting]
        VALIDATE --> MYPY[Type Checking]
        VALIDATE --> PYTEST[Unit Tests]
    end
    
    subgraph "Deployment Steps"
        DEPLOY_INFRA --> CREATE_TABLES[Create Tables]
        DEPLOY_INFRA --> CREATE_FUNCTIONS[Create Functions]
        DEPLOY_INFRA --> SETUP_TELEMETRY[Setup Telemetry]
    end
    
    subgraph "Testing Steps"
        PERF_TEST --> LATENCY_TEST[Latency Testing]
        PERF_TEST --> SUCCESS_RATE[Success Rate Check]
        PERF_TEST --> COST_ANALYSIS[Cost Analysis]
    end
```

## Query Processing Detailed Flow

```mermaid
stateDiagram-v2
    [*] --> QueryReceived
    QueryReceived --> ValidateInput
    ValidateInput --> GenerateQueryEmbedding
    
    GenerateQueryEmbedding --> EmbeddingSuccess
    GenerateQueryEmbedding --> EmbeddingError
    
    EmbeddingSuccess --> PerformSimilaritySearch
    EmbeddingError --> LogError
    LogError --> [*]
    
    PerformSimilaritySearch --> SearchResults
    SearchResults --> BuildContext
    BuildContext --> GeneratePrompt
    
    GeneratePrompt --> LLMCompletion
    LLMCompletion --> CompletionSuccess
    LLMCompletion --> CompletionError
    
    CompletionSuccess --> LogTelemetry
    CompletionError --> LogError
    
    LogTelemetry --> StoreQueryHistory
    StoreQueryHistory --> ReturnResponse
    ReturnResponse --> [*]
    
    note right of ValidateInput
        Input sanitization
        Length validation
        Content filtering
    end note
    
    note right of PerformSimilaritySearch
        VECTOR_COSINE_SIMILARITY
        Top-K selection
        Threshold filtering
    end note
    
    note right of LLMCompletion
        CORTEX.COMPLETE
        Context injection
        Parameter optimization
    end note
```

---

## ASCII Flow Diagrams (Viewable in Text Editor)

### Main Pipeline Flow

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   PDF/DOCX  │───►│   INGESTION  │───►│   CHUNKING  │───►│  VALIDATION  │
│    Files    │    │ ingest_loader│    │   & CLEAN   │    │   & STORE    │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
                                                                    │
                                                                    ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│ User Query  │───►│Query Embedding│───►│Vector Search│◄───┤ RAW_DOCUMENTS│
│             │    │CORTEX.EMBED  │    │COSINE_SIMILARITY│ │    TABLE     │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
      │                                         │                  │
      │                                         ▼                  ▼
      │            ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
      │            │   CONTEXT    │◄───┤ TOP-K CHUNKS│◄───┤  EMBEDDINGS  │
      │            │  BUILDING    │    │   SIMILAR   │    │    TABLE     │
      │            └──────────────┘    └─────────────┘    └──────────────┘
      │                     │
      ▼                     ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   PROMPT    │───►│CORTEX.COMPLETE│───►│  RESPONSE   │───►│QUERY HISTORY │
│ ENHANCEMENT │    │    (LLM)     │    │ GENERATION  │    │    TABLE     │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
                            │                   │                  │
                            ▼                   ▼                  ▼
                   ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
                   │  TELEMETRY   │    │  TELEMETRY  │    │  TELEMETRY   │
                   │  (Latency)   │    │   (Costs)   │    │ (Success)    │
                   └──────────────┘    └─────────────┘    └──────────────┘
                            │                   │                  │
                            └───────────────────┼──────────────────┘
                                               ▼
                                    ┌──────────────┐
                                    │  STREAMLIT   │
                                    │  DASHBOARD   │
                                    └──────────────┘
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SNOWFLAKE CORTEX GENAI PIPELINE                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │    utils    │  │ingest_loader│  │embed_generator│ │cortex_query │   │
│  │   .py       │  │    .py      │  │    .py      │  │    .py      │   │
│  │             │  │             │  │             │  │             │   │
│  │• Connection │  │• Doc Upload │  │• Embedding  │  │• Semantic   │   │
│  │• Config     │  │• Text Extract│  │• Vector Gen │  │• Search     │   │
│  │• Logging    │  │• Validation │  │• Storage    │  │• LLM Query  │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│         │                 │                 │                 │       │
│         └─────────────────┼─────────────────┼─────────────────┘       │
│                           │                 │                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │telemetry_   │  │dashboard_   │  │             │  │             │   │
│  │  task.py    │  │  plot.py    │  │   CONFIG/   │  │NOTEBOOKS/   │   │
│  │             │  │             │  │             │  │             │   │
│  │• Metrics    │  │• Streamlit  │  │• snowflake  │  │• SQL Demo   │   │
│  │• Monitoring │  │• Charts     │  │• .env       │  │• Examples   │   │
│  │• Costs      │  │• Analytics  │  │• logging    │  │• Tests      │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
            ┌─────────────────────────────────────────────────┐
            │             SNOWFLAKE CORTEX FUNCTIONS          │
            ├─────────────────────────────────────────────────┤
            │                                                 │
            │  CORTEX.EMBED_TEXT_768()  │  CORTEX.COMPLETE()  │
            │  • Text → Vector          │  • Prompt → Text    │
            │  • 768 dimensions         │  • Multiple Models  │
            │  • Multilingual           │  • Context Aware    │
            │                          │                     │
            │     VECTOR_COSINE_SIMILARITY()                  │
            │     • Semantic Search                           │
            │     • Relevance Ranking                         │
            │     • Fast Vector Ops                           │
            └─────────────────────────────────────────────────┘
```

### Data Flow Process

```
INPUT DOCUMENTS
       │
       ▼
┌─────────────┐
│ Text Extract│ ───► Split into chunks ───► Validate content
└─────────────┘
       │
       ▼
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│Store in RAW │────────►│Generate     │────────►│Store Vector │
│Documents    │         │Embeddings   │         │Embeddings   │
│Table        │         │CORTEX.EMBED │         │Table        │
└─────────────┘         └─────────────┘         └─────────────┘
                                                        │
                                                        │
USER QUERY                                              │
    │                                                   │
    ▼                                                   │
┌─────────────┐         ┌─────────────┐                │
│Embed Query  │────────►│Find Similar │◄───────────────┘
│CORTEX.EMBED │         │Chunks       │
└─────────────┘         │COSINE_SIM   │
                        └─────────────┘
                                │
                                ▼
                        ┌─────────────┐
                        │Build Context│
                        │from Top-K   │
                        │Chunks       │
                        └─────────────┘
                                │
                                ▼
                        ┌─────────────┐         ┌─────────────┐
                        │Enhanced     │────────►│LLM Response │
                        │Prompt       │         │CORTEX.      │
                        │             │         │COMPLETE     │
                        └─────────────┘         └─────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────┐
                                                │Return to    │
                                                │User +       │
                                                │Log Metrics  │
                                                └─────────────┘
```

### Telemetry & Monitoring Flow

```
OPERATIONS                    TELEMETRY COLLECTION              STORAGE
     │                             │                              │
┌────▼────┐                 ┌──────▼──────┐              ┌──────▼──────┐
│Ingestion│────────────────►│TelemetryTask│─────────────►│Telemetry    │
├─────────┤                 ├─────────────┤              │Table        │
│Embedding│────────────────►│• Latency    │              ├─────────────┤
├─────────┤                 │• Costs      │              │• Performance│
│Search   │────────────────►│• Success    │              │• Costs      │
├─────────┤                 │• Errors     │              │• Errors     │
│LLM Call │────────────────►│• Batch      │              │• Trends     │
└─────────┘                 └─────────────┘              └─────────────┘
                                   │                              │
                                   ▼                              ▼
                            ┌─────────────┐              ┌─────────────┐
                            │Real-time    │◄─────────────┤Dashboard    │
                            │Alerts       │              │Analytics    │
                            │• Failures   │              │• Charts     │
                            │• High Costs │              │• Metrics    │
                            │• Latency    │              │• Reports    │
                            └─────────────┘              └─────────────┘
```

### File Structure Tree

```
snowflake_genai_demo/
├── src/
│   ├── utils.py              # Core utilities & connection management
│   ├── ingest_loader.py      # Document ingestion pipeline  
│   ├── embed_generator.py    # Embedding generation with Cortex
│   ├── cortex_query.py       # Semantic search & LLM completion
│   ├── telemetry_task.py     # Performance monitoring & metrics
│   └── dashboard_plot.py     # Streamlit analytics dashboard
│
├── config/
│   ├── snowflake.yaml       # Database connection config
│   ├── logging.yaml         # Logging configuration
│   └── .env.template        # Environment variables template
│
├── notebooks/
│   └── cortex_demo.ipynb    # SQL demo and examples
│
├── docs/
│   ├── README.md            # Complete project documentation
│   ├── flow_diagram.md      # Mermaid flow diagrams
│   └── presentation.md      # Project presentation content
│
├── pipelines/
│   └── deploy.yaml          # CI/CD GitHub Actions pipeline
│
├── prompts/
│   └── github_copilot.md    # AI assistant prompts
│
└── requirements.txt         # Python dependencies
```
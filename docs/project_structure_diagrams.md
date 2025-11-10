# Snowflake Cortex GenAI Pipeline - Project Structure and Component Overview

## Project Structure Visualization

```mermaid
graph TB
    subgraph "Project Root: snowflake_genai_demo/"
        ROOT[snowflake_genai_demo/]
        
        subgraph "Source Code (src/)"
            UTILS[utils.py<br/>Database connections<br/>Utility functions<br/>Configuration management]
            INGEST[ingest_loader.py<br/>Document ingestion<br/>File processing<br/>Text extraction]
            EMBED[embed_generator.py<br/>Vector embeddings<br/>CORTEX.EMBED_TEXT_768<br/>Batch processing]
            QUERY[cortex_query.py<br/>Semantic search<br/>LLM completion<br/>Query processing]
            TELEMETRY[telemetry_task.py<br/>Performance monitoring<br/>Cost tracking<br/>Error logging]
            DASHBOARD[dashboard_plot.py<br/>Streamlit interface<br/>Analytics visualization<br/>Interactive queries]
        end
        
        subgraph "Configuration (config/)"
            CREDS[creds.env<br/>Snowflake credentials<br/>Database connection]
            SETTINGS[settings.yaml<br/>Pipeline configuration<br/>Model parameters]
            SNOWFLAKE_CONFIG[snowflake.toml<br/>Connection profiles<br/>Environment settings]
        end
        
        subgraph "Documentation (docs/)"
            FLOW_DIAGRAM[flow_diagram.md<br/>System architecture<br/>Mermaid diagrams]
            ASCII_DIAGRAM[ascii_flow_diagram.md<br/>Text-based diagrams<br/>Command-line friendly]
            DETAILED_ARCH[detailed_architecture_diagrams.md<br/>Comprehensive diagrams<br/>System design]
        end
        
        subgraph "Notebooks (notebooks/)"
            CORTEX_SQL[cortex_pipeline.sql<br/>SQL demonstrations<br/>Cortex function examples<br/>Database setup]
        end
        
        subgraph "CI/CD (pipelines/)"
            DEPLOY[deploy.yaml<br/>GitHub Actions<br/>Automated deployment<br/>Testing pipeline]
        end
        
        subgraph "Prompts (prompts/)"
            SYSTEM[system_prompt.txt<br/>LLM system prompts<br/>Behavior guidelines]
            COPILOT[copilot_task_prompt.txt<br/>GitHub Copilot integration<br/>Development assistance]
            TELEMETRY_PROMPT[telemetry_prompt.txt<br/>Monitoring prompts<br/>Alert templates]
        end
        
        subgraph "Sample Data (sample_data/)"
            COMPANY_DOCS[company_docs.md<br/>Test documents<br/>Sample content<br/>Demo data]
        end
        
        subgraph "Presentations (slides/)"
            ARCH_CONTENT[Snowflake_Cortex_Architecture_Content.md<br/>Architecture presentation<br/>Technical overview<br/>System explanation]
        end
        
        subgraph "Test Scripts"
            TEST_CONNECTION[test_connection.py<br/>Database connectivity<br/>Credential validation<br/>Environment check]
            TEST_PIPELINE[test_pipeline_demo.py<br/>End-to-end testing<br/>Pipeline validation<br/>Demo execution]
        end
        
        subgraph "Project Files"
            REQUIREMENTS[requirements.txt<br/>Python dependencies<br/>Package versions]
            README_FILE[README.md<br/>Project documentation<br/>Usage instructions]
            STATUS[STATUS.md<br/>Project status<br/>Implementation progress]
        end
    end
    
    %% Component Dependencies
    UTILS --> INGEST
    UTILS --> EMBED
    UTILS --> QUERY
    UTILS --> TELEMETRY
    UTILS --> DASHBOARD
    
    CREDS --> UTILS
    SETTINGS --> UTILS
    SNOWFLAKE_CONFIG --> UTILS
    
    INGEST --> EMBED
    EMBED --> QUERY
    QUERY --> TELEMETRY
    TELEMETRY --> DASHBOARD
    
    TEST_CONNECTION --> UTILS
    TEST_PIPELINE --> INGEST
    TEST_PIPELINE --> EMBED
    TEST_PIPELINE --> QUERY
    
    CORTEX_SQL --> QUERY
    DEPLOY --> TEST_CONNECTION
    DEPLOY --> TEST_PIPELINE
    
    SYSTEM --> QUERY
    COPILOT --> UTILS
    TELEMETRY_PROMPT --> TELEMETRY
    
    COMPANY_DOCS --> INGEST
    ARCH_CONTENT --> FLOW_DIAGRAM
    
    %% Styling
    classDef source fill:#e3f2fd
    classDef config fill:#f3e5f5
    classDef docs fill:#fff3e0
    classDef notebooks fill:#e8f5e8
    classDef cicd fill:#f1f8e9
    classDef prompts fill:#fce4ec
    classDef data fill:#e0f2f1
    classDef slides fill:#f9fbe7
    classDef tests fill:#fff8e1
    classDef project fill:#fafafa
    
    class UTILS,INGEST,EMBED,QUERY,TELEMETRY,DASHBOARD source
    class CREDS,SETTINGS,SNOWFLAKE_CONFIG config
    class FLOW_DIAGRAM,ASCII_DIAGRAM,DETAILED_ARCH docs
    class CORTEX_SQL notebooks
    class DEPLOY cicd
    class SYSTEM,COPILOT,TELEMETRY_PROMPT prompts
    class COMPANY_DOCS data
    class ARCH_CONTENT slides
    class TEST_CONNECTION,TEST_PIPELINE tests
    class REQUIREMENTS,README_FILE,STATUS project
```

## Component Interaction Map

```mermaid
graph LR
    subgraph "User Interfaces"
        CLI[Command Line Interface]
        WEB[Web Dashboard]
        NOTEBOOK[SQL Notebook]
    end
    
    subgraph "Core Processing Pipeline"
        INGEST_LAYER[Document Ingestion Layer]
        EMBED_LAYER[Embedding Generation Layer]  
        QUERY_LAYER[Query Processing Layer]
        MONITOR_LAYER[Monitoring Layer]
    end
    
    subgraph "Snowflake Cortex Services"
        EMBED_SERVICE[CORTEX.EMBED_TEXT_768]
        COMPLETE_SERVICE[CORTEX.COMPLETE]
        SIMILARITY_SERVICE[VECTOR_COSINE_SIMILARITY]
    end
    
    subgraph "Data Storage"
        RAW_STORAGE[(media_raw)]
        VECTOR_STORAGE[(media_embeddings)]
        QUERY_STORAGE[(query_history)]
        TELEMETRY_STORAGE[(genai_telemetry)]
    end
    
    subgraph "Configuration Management"
        ENV_CONFIG[Environment Configuration]
        MODEL_CONFIG[Model Configuration]
        PIPELINE_CONFIG[Pipeline Configuration]
    end
    
    %% User Interface Connections
    CLI --> INGEST_LAYER
    CLI --> QUERY_LAYER
    CLI --> MONITOR_LAYER
    WEB --> QUERY_LAYER
    WEB --> MONITOR_LAYER
    NOTEBOOK --> QUERY_LAYER
    
    %% Core Pipeline Flow
    INGEST_LAYER --> RAW_STORAGE
    RAW_STORAGE --> EMBED_LAYER
    EMBED_LAYER --> EMBED_SERVICE
    EMBED_SERVICE --> VECTOR_STORAGE
    
    QUERY_LAYER --> EMBED_SERVICE
    QUERY_LAYER --> SIMILARITY_SERVICE
    SIMILARITY_SERVICE --> VECTOR_STORAGE
    QUERY_LAYER --> COMPLETE_SERVICE
    QUERY_LAYER --> QUERY_STORAGE
    
    %% Monitoring Connections
    INGEST_LAYER --> MONITOR_LAYER
    EMBED_LAYER --> MONITOR_LAYER
    QUERY_LAYER --> MONITOR_LAYER
    MONITOR_LAYER --> TELEMETRY_STORAGE
    
    %% Configuration Connections
    ENV_CONFIG --> INGEST_LAYER
    ENV_CONFIG --> EMBED_LAYER
    ENV_CONFIG --> QUERY_LAYER
    ENV_CONFIG --> MONITOR_LAYER
    
    MODEL_CONFIG --> EMBED_LAYER
    MODEL_CONFIG --> QUERY_LAYER
    
    PIPELINE_CONFIG --> INGEST_LAYER
    PIPELINE_CONFIG --> EMBED_LAYER
    PIPELINE_CONFIG --> QUERY_LAYER
    
    %% Styling
    classDef interface fill:#e3f2fd
    classDef processing fill:#f3e5f5
    classDef cortex fill:#e8f5e8
    classDef storage fill:#fff3e0
    classDef config fill:#fafafa
    
    class CLI,WEB,NOTEBOOK interface
    class INGEST_LAYER,EMBED_LAYER,QUERY_LAYER,MONITOR_LAYER processing
    class EMBED_SERVICE,COMPLETE_SERVICE,SIMILARITY_SERVICE cortex
    class RAW_STORAGE,VECTOR_STORAGE,QUERY_STORAGE,TELEMETRY_STORAGE storage
    class ENV_CONFIG,MODEL_CONFIG,PIPELINE_CONFIG config
```

## Module Responsibility Matrix

| Module | Primary Function | Input | Output | Dependencies |
|--------|------------------|--------|---------|--------------|
| `utils.py` | Database connection management | Configuration files | Database connections | snowflake-connector-python |
| `ingest_loader.py` | Document processing and ingestion | PDF, DOCX, TXT, MD files | Structured text chunks | utils.py, PyPDF2, python-docx |
| `embed_generator.py` | Vector embedding generation | Text chunks | Vector embeddings | utils.py, CORTEX.EMBED_TEXT_768 |
| `cortex_query.py` | Query processing and response | User queries | Generated responses | utils.py, embed_generator.py |
| `telemetry_task.py` | Performance monitoring | System metrics | Telemetry data | utils.py, all processing modules |
| `dashboard_plot.py` | Analytics visualization | Telemetry data | Interactive dashboard | streamlit, plotly, utils.py |

## Data Flow Specification

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant IngestLoader
    participant EmbedGenerator  
    participant CortexQuery
    participant TelemetryTask
    participant Dashboard
    participant SnowflakeDB
    
    Note over User,SnowflakeDB: Document Processing Flow
    
    User->>CLI: Upload Documents
    CLI->>IngestLoader: Process Files
    IngestLoader->>SnowflakeDB: Store Raw Text
    IngestLoader->>TelemetryTask: Log Ingestion Metrics
    
    Note over User,SnowflakeDB: Embedding Generation Flow
    
    CLI->>EmbedGenerator: Generate Embeddings
    EmbedGenerator->>SnowflakeDB: CORTEX.EMBED_TEXT_768()
    SnowflakeDB->>EmbedGenerator: Vector Data
    EmbedGenerator->>SnowflakeDB: Store Embeddings
    EmbedGenerator->>TelemetryTask: Log Embedding Metrics
    
    Note over User,SnowflakeDB: Query Processing Flow
    
    User->>CLI: Submit Query
    CLI->>CortexQuery: Process Query
    CortexQuery->>SnowflakeDB: Generate Query Embedding
    CortexQuery->>SnowflakeDB: Semantic Search
    CortexQuery->>SnowflakeDB: LLM Completion
    SnowflakeDB->>CortexQuery: Final Response
    CortexQuery->>CLI: Return Answer
    CLI->>User: Display Response
    CortexQuery->>TelemetryTask: Log Query Metrics
    
    Note over User,SnowflakeDB: Monitoring and Analytics
    
    TelemetryTask->>SnowflakeDB: Store Metrics
    User->>Dashboard: View Analytics
    Dashboard->>SnowflakeDB: Query Metrics
    SnowflakeDB->>Dashboard: Return Data
    Dashboard->>User: Display Insights
```

## Configuration Architecture

```mermaid
graph TB
    subgraph "Configuration Sources"
        ENV_FILE[.env File<br/>Credentials & Secrets]
        YAML_FILE[settings.yaml<br/>Application Settings]
        TOML_FILE[snowflake.toml<br/>Connection Profiles]
        ARGS[Command Line Arguments<br/>Runtime Parameters]
    end
    
    subgraph "Configuration Processor"
        CONFIG_LOADER[Configuration Loader]
        VALIDATOR[Configuration Validator]
        MERGER[Configuration Merger]
        RESOLVER[Variable Resolver]
    end
    
    subgraph "Configuration Consumer Modules"
        CONNECTION_MGR[Connection Manager]
        PIPELINE_CONFIG[Pipeline Configuration]
        MODEL_CONFIG[Model Configuration]
        LOGGING_CONFIG[Logging Configuration]
    end
    
    subgraph "Runtime Configuration"
        ACTIVE_CONFIG[Active Configuration]
        CACHE[Configuration Cache]
        MONITOR[Configuration Monitor]
    end
    
    %% Configuration Flow
    ENV_FILE --> CONFIG_LOADER
    YAML_FILE --> CONFIG_LOADER
    TOML_FILE --> CONFIG_LOADER
    ARGS --> CONFIG_LOADER
    
    CONFIG_LOADER --> VALIDATOR
    VALIDATOR --> MERGER
    MERGER --> RESOLVER
    
    RESOLVER --> CONNECTION_MGR
    RESOLVER --> PIPELINE_CONFIG
    RESOLVER --> MODEL_CONFIG
    RESOLVER --> LOGGING_CONFIG
    
    CONNECTION_MGR --> ACTIVE_CONFIG
    PIPELINE_CONFIG --> ACTIVE_CONFIG
    MODEL_CONFIG --> ACTIVE_CONFIG
    LOGGING_CONFIG --> ACTIVE_CONFIG
    
    ACTIVE_CONFIG --> CACHE
    CACHE --> MONITOR
    
    %% Styling
    classDef source fill:#e3f2fd
    classDef processor fill:#f3e5f5
    classDef consumer fill:#e8f5e8
    classDef runtime fill:#fff3e0
    
    class ENV_FILE,YAML_FILE,TOML_FILE,ARGS source
    class CONFIG_LOADER,VALIDATOR,MERGER,RESOLVER processor
    class CONNECTION_MGR,PIPELINE_CONFIG,MODEL_CONFIG,LOGGING_CONFIG consumer
    class ACTIVE_CONFIG,CACHE,MONITOR runtime
```

## Execution Modes and Entry Points

```mermaid
graph LR
    subgraph "Execution Modes"
        STANDALONE[Standalone Scripts]
        INTERACTIVE[Interactive Mode]
        BATCH[Batch Processing]
        DAEMON[Daemon Mode]
        TEST[Test Mode]
    end
    
    subgraph "Entry Points"
        CLI_INGEST[python src/ingest_loader.py]
        CLI_EMBED[python src/embed_generator.py]
        CLI_QUERY[python src/cortex_query.py]
        CLI_TELEMETRY[python src/telemetry_task.py]
        CLI_DASHBOARD[streamlit run src/dashboard_plot.py]
        CLI_TEST[python test_pipeline_demo.py]
    end
    
    subgraph "Execution Context"
        DEV_CONTEXT[Development Context]
        PROD_CONTEXT[Production Context]
        DEMO_CONTEXT[Demo Context]
        TEST_CONTEXT[Test Context]
    end
    
    %% Mode Mappings
    STANDALONE --> CLI_INGEST
    STANDALONE --> CLI_EMBED
    STANDALONE --> CLI_QUERY
    STANDALONE --> CLI_TELEMETRY
    
    INTERACTIVE --> CLI_DASHBOARD
    INTERACTIVE --> CLI_QUERY
    
    BATCH --> CLI_INGEST
    BATCH --> CLI_EMBED
    
    DAEMON --> CLI_TELEMETRY
    DAEMON --> CLI_DASHBOARD
    
    TEST --> CLI_TEST
    
    %% Context Mappings
    CLI_INGEST --> DEV_CONTEXT
    CLI_INGEST --> PROD_CONTEXT
    
    CLI_EMBED --> DEV_CONTEXT
    CLI_EMBED --> PROD_CONTEXT
    
    CLI_QUERY --> DEV_CONTEXT
    CLI_QUERY --> PROD_CONTEXT
    CLI_QUERY --> DEMO_CONTEXT
    
    CLI_TELEMETRY --> PROD_CONTEXT
    
    CLI_DASHBOARD --> DEV_CONTEXT
    CLI_DASHBOARD --> PROD_CONTEXT
    CLI_DASHBOARD --> DEMO_CONTEXT
    
    CLI_TEST --> TEST_CONTEXT
    CLI_TEST --> DEMO_CONTEXT
    
    %% Styling
    classDef mode fill:#e3f2fd
    classDef entry fill:#f3e5f5
    classDef context fill:#e8f5e8
    
    class STANDALONE,INTERACTIVE,BATCH,DAEMON,TEST mode
    class CLI_INGEST,CLI_EMBED,CLI_QUERY,CLI_TELEMETRY,CLI_DASHBOARD,CLI_TEST entry
    class DEV_CONTEXT,PROD_CONTEXT,DEMO_CONTEXT,TEST_CONTEXT context
```

This comprehensive project structure documentation provides:

1. **Visual Project Structure**: Complete file organization and dependencies
2. **Component Interaction Map**: How modules communicate with each other
3. **Module Responsibility Matrix**: Clear definition of each module's role
4. **Data Flow Specification**: Sequence of operations across the system
5. **Configuration Architecture**: How settings and configuration are managed
6. **Execution Modes**: Different ways to run the system

Each diagram uses consistent styling and provides clear visibility into the system architecture and component relationships.
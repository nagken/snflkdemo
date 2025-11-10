# Snowflake Cortex GenAI Pipeline - Detailed Architecture Diagrams

## System Overview

This document provides comprehensive architectural diagrams for the Snowflake Cortex GenAI Pipeline, illustrating the complete data flow, component interactions, and deployment architecture.

## 1. High-Level System Architecture

```mermaid
graph TB
    %% External Interfaces
    USER[User Interface] --> API_GATEWAY[API Gateway]
    FILES[Document Files] --> UPLOAD[File Upload Service]
    
    %% Application Layer
    subgraph "Application Services"
        API_GATEWAY --> QUERY_SVC[Query Service]
        API_GATEWAY --> INGEST_SVC[Ingestion Service]
        API_GATEWAY --> MONITOR_SVC[Monitoring Service]
        
        QUERY_SVC --> CORTEX_QUERY[cortex_query.py]
        INGEST_SVC --> INGEST_LOADER[ingest_loader.py]
        INGEST_SVC --> EMBED_GEN[embed_generator.py]
        MONITOR_SVC --> TELEMETRY[telemetry_task.py]
    end
    
    %% Processing Layer
    subgraph "Processing Pipeline"
        CORTEX_QUERY --> SEARCH_ENGINE[Semantic Search Engine]
        CORTEX_QUERY --> LLM_ENGINE[LLM Completion Engine]
        INGEST_LOADER --> TEXT_PROC[Text Processing]
        EMBED_GEN --> VECTOR_PROC[Vector Processing]
        
        TEXT_PROC --> CHUNK_ENGINE[Chunking Engine]
        VECTOR_PROC --> EMBED_ENGINE[Embedding Engine]
    end
    
    %% Snowflake Cortex Layer
    subgraph "Snowflake Cortex Services"
        EMBED_ENGINE --> CORTEX_EMBED[CORTEX.EMBED_TEXT_768]
        LLM_ENGINE --> CORTEX_COMPLETE[CORTEX.COMPLETE]
        SEARCH_ENGINE --> VECTOR_SIMILARITY[VECTOR_COSINE_SIMILARITY]
    end
    
    %% Data Storage Layer
    subgraph "Snowflake Database"
        CORTEX_EMBED --> EMBED_TABLE[(media_embeddings)]
        CORTEX_COMPLETE --> QUERY_HIST[(query_history)]
        CHUNK_ENGINE --> RAW_TABLE[(media_raw)]
        TELEMETRY --> METRICS_TABLE[(genai_telemetry)]
        
        EMBED_TABLE --> VECTOR_SIMILARITY
        RAW_TABLE --> EMBED_GEN
    end
    
    %% Analytics Layer
    subgraph "Analytics & Monitoring"
        METRICS_TABLE --> DASHBOARD[Streamlit Dashboard]
        DASHBOARD --> PERF_VIZ[Performance Visualization]
        DASHBOARD --> COST_VIZ[Cost Analysis]
        DASHBOARD --> ERROR_VIZ[Error Monitoring]
    end
    
    %% Configuration Management
    subgraph "Configuration"
        CONFIG[config/settings.yaml] --> CORTEX_QUERY
        CONFIG --> INGEST_LOADER
        CONFIG --> EMBED_GEN
        CREDS[config/creds.env] --> UTILS[src/utils.py]
        UTILS --> CORTEX_QUERY
        UTILS --> INGEST_LOADER
        UTILS --> EMBED_GEN
    end
    
    %% CI/CD Pipeline
    subgraph "Deployment"
        GITHUB[GitHub Repository] --> ACTIONS[GitHub Actions]
        ACTIONS --> DEPLOY[pipelines/deploy.yaml]
        DEPLOY --> SNOWFLAKE_DEPLOY[Snowflake Deployment]
    end
    
    %% Styling
    classDef user fill:#e3f2fd
    classDef service fill:#f3e5f5
    classDef processing fill:#fff3e0
    classDef cortex fill:#e8f5e8
    classDef storage fill:#fce4ec
    classDef analytics fill:#f1f8e9
    classDef config fill:#fafafa
    classDef deployment fill:#e0f2f1
    
    class USER,FILES user
    class API_GATEWAY,QUERY_SVC,INGEST_SVC,MONITOR_SVC service
    class CORTEX_QUERY,INGEST_LOADER,EMBED_GEN,TELEMETRY,SEARCH_ENGINE,LLM_ENGINE,TEXT_PROC,VECTOR_PROC,CHUNK_ENGINE,EMBED_ENGINE processing
    class CORTEX_EMBED,CORTEX_COMPLETE,VECTOR_SIMILARITY cortex
    class EMBED_TABLE,QUERY_HIST,RAW_TABLE,METRICS_TABLE storage
    class DASHBOARD,PERF_VIZ,COST_VIZ,ERROR_VIZ analytics
    class CONFIG,CREDS,UTILS config
    class GITHUB,ACTIONS,DEPLOY,SNOWFLAKE_DEPLOY deployment
```

## 2. Document Ingestion Pipeline

```mermaid
flowchart TD
    %% Input Sources
    subgraph "Document Sources"
        PDF[PDF Files]
        DOCX[Word Documents]
        TXT[Text Files]
        MD[Markdown Files]
        API_DOC[API Documents]
    end
    
    %% File Processing
    subgraph "File Processing Layer"
        UPLOAD[File Upload Handler]
        VALIDATION[File Validation]
        TYPE_DETECT[File Type Detection]
        SIZE_CHECK[Size Validation]
        FORMAT_CHECK[Format Validation]
    end
    
    %% Content Extraction
    subgraph "Content Extraction"
        PDF_EXTRACT[PDF Text Extraction]
        DOCX_EXTRACT[DOCX Text Extraction]
        TXT_EXTRACT[Plain Text Handler]
        MD_EXTRACT[Markdown Parser]
        CLEAN_TEXT[Text Cleaning]
    end
    
    %% Text Processing
    subgraph "Text Processing Pipeline"
        NORMALIZE[Text Normalization]
        TOKENIZE[Tokenization]
        CHUNK_SPLIT[Intelligent Chunking]
        OVERLAP[Overlap Management]
        METADATA[Metadata Extraction]
    end
    
    %% Quality Control
    subgraph "Quality Assurance"
        CONTENT_VAL[Content Validation]
        DUPLICATE[Duplicate Detection]
        QUALITY_SCORE[Quality Scoring]
        FILTER[Content Filtering]
    end
    
    %% Storage Preparation
    subgraph "Storage Preparation"
        SERIALIZE[Data Serialization]
        BATCH_PREP[Batch Preparation]
        COMPRESS[Compression]
    end
    
    %% Data Storage
    subgraph "Snowflake Storage"
        RAW_INSERT[Raw Data Insert]
        STAGING_TABLE[(staging_documents)]
        RAW_TABLE[(media_raw)]
        INDEX_UPDATE[Index Updates]
    end
    
    %% Monitoring
    subgraph "Process Monitoring"
        INGEST_METRICS[Ingestion Metrics]
        ERROR_HANDLE[Error Handling]
        RETRY_LOGIC[Retry Mechanism]
        TELEMETRY_LOG[Telemetry Logging]
    end
    
    %% Flow Connections
    PDF --> UPLOAD
    DOCX --> UPLOAD
    TXT --> UPLOAD
    MD --> UPLOAD
    API_DOC --> UPLOAD
    
    UPLOAD --> VALIDATION
    VALIDATION --> TYPE_DETECT
    TYPE_DETECT --> SIZE_CHECK
    SIZE_CHECK --> FORMAT_CHECK
    
    FORMAT_CHECK --> PDF_EXTRACT
    FORMAT_CHECK --> DOCX_EXTRACT
    FORMAT_CHECK --> TXT_EXTRACT
    FORMAT_CHECK --> MD_EXTRACT
    
    PDF_EXTRACT --> CLEAN_TEXT
    DOCX_EXTRACT --> CLEAN_TEXT
    TXT_EXTRACT --> CLEAN_TEXT
    MD_EXTRACT --> CLEAN_TEXT
    
    CLEAN_TEXT --> NORMALIZE
    NORMALIZE --> TOKENIZE
    TOKENIZE --> CHUNK_SPLIT
    CHUNK_SPLIT --> OVERLAP
    OVERLAP --> METADATA
    
    METADATA --> CONTENT_VAL
    CONTENT_VAL --> DUPLICATE
    DUPLICATE --> QUALITY_SCORE
    QUALITY_SCORE --> FILTER
    
    FILTER --> SERIALIZE
    SERIALIZE --> BATCH_PREP
    BATCH_PREP --> COMPRESS
    
    COMPRESS --> RAW_INSERT
    RAW_INSERT --> STAGING_TABLE
    STAGING_TABLE --> RAW_TABLE
    RAW_TABLE --> INDEX_UPDATE
    
    %% Monitoring Connections
    UPLOAD --> INGEST_METRICS
    PDF_EXTRACT --> ERROR_HANDLE
    DOCX_EXTRACT --> ERROR_HANDLE
    TXT_EXTRACT --> ERROR_HANDLE
    MD_EXTRACT --> ERROR_HANDLE
    ERROR_HANDLE --> RETRY_LOGIC
    RETRY_LOGIC --> TELEMETRY_LOG
    
    %% Styling
    classDef input fill:#e1f5fe
    classDef processing fill:#f3e5f5
    classDef quality fill:#fff3e0
    classDef storage fill:#e8f5e8
    classDef monitoring fill:#fce4ec
    
    class PDF,DOCX,TXT,MD,API_DOC input
    class UPLOAD,VALIDATION,TYPE_DETECT,SIZE_CHECK,FORMAT_CHECK,PDF_EXTRACT,DOCX_EXTRACT,TXT_EXTRACT,MD_EXTRACT,CLEAN_TEXT,NORMALIZE,TOKENIZE,CHUNK_SPLIT,OVERLAP,METADATA processing
    class CONTENT_VAL,DUPLICATE,QUALITY_SCORE,FILTER quality
    class SERIALIZE,BATCH_PREP,COMPRESS,RAW_INSERT,STAGING_TABLE,RAW_TABLE,INDEX_UPDATE storage
    class INGEST_METRICS,ERROR_HANDLE,RETRY_LOGIC,TELEMETRY_LOG monitoring
```

## 3. Vector Embedding Pipeline

```mermaid
graph TD
    %% Input Layer
    subgraph "Data Input"
        RAW_DATA[(media_raw)]
        CHUNK_QUEUE[Chunked Text Queue]
        BATCH_PROCESSOR[Batch Processor]
    end
    
    %% Processing Layer
    subgraph "Embedding Generation"
        PREPROCESS[Text Preprocessing]
        TOKEN_LIMIT[Token Limit Check]
        BATCH_MANAGER[Batch Manager]
        EMBED_REQUEST[Embedding Request]
        CORTEX_API[CORTEX.EMBED_TEXT_768]
        VECTOR_VALIDATE[Vector Validation]
        DIMENSION_CHECK[Dimension Verification]
    end
    
    %% Storage Layer
    subgraph "Vector Storage"
        VECTOR_PREP[Vector Preparation]
        METADATA_LINK[Metadata Linking]
        EMBED_INSERT[Embedding Insert]
        EMBED_TABLE[(media_embeddings)]
        INDEX_BUILD[Vector Index Build]
    end
    
    %% Quality Control
    subgraph "Quality Assurance"
        SIMILARITY_CHECK[Similarity Validation]
        OUTLIER_DETECT[Outlier Detection]
        QUALITY_METRICS[Quality Metrics]
    end
    
    %% Performance Monitoring
    subgraph "Performance Tracking"
        LATENCY_TRACK[Latency Tracking]
        THROUGHPUT_MONITOR[Throughput Monitor]
        COST_TRACK[Cost Tracking]
        ERROR_MONITOR[Error Monitoring]
        PERF_TELEMETRY[Performance Telemetry]
    end
    
    %% Optimization Layer
    subgraph "Optimization"
        CACHE_LAYER[Embedding Cache]
        DEDUP_CHECK[Deduplication Check]
        COMPRESSION[Vector Compression]
        PARALLEL_PROC[Parallel Processing]
    end
    
    %% Flow Connections
    RAW_DATA --> CHUNK_QUEUE
    CHUNK_QUEUE --> BATCH_PROCESSOR
    BATCH_PROCESSOR --> PREPROCESS
    
    PREPROCESS --> TOKEN_LIMIT
    TOKEN_LIMIT --> BATCH_MANAGER
    BATCH_MANAGER --> EMBED_REQUEST
    EMBED_REQUEST --> CORTEX_API
    CORTEX_API --> VECTOR_VALIDATE
    VECTOR_VALIDATE --> DIMENSION_CHECK
    
    DIMENSION_CHECK --> VECTOR_PREP
    VECTOR_PREP --> METADATA_LINK
    METADATA_LINK --> EMBED_INSERT
    EMBED_INSERT --> EMBED_TABLE
    EMBED_TABLE --> INDEX_BUILD
    
    %% Quality Connections
    VECTOR_VALIDATE --> SIMILARITY_CHECK
    SIMILARITY_CHECK --> OUTLIER_DETECT
    OUTLIER_DETECT --> QUALITY_METRICS
    
    %% Performance Connections
    CORTEX_API --> LATENCY_TRACK
    BATCH_MANAGER --> THROUGHPUT_MONITOR
    CORTEX_API --> COST_TRACK
    EMBED_REQUEST --> ERROR_MONITOR
    LATENCY_TRACK --> PERF_TELEMETRY
    THROUGHPUT_MONITOR --> PERF_TELEMETRY
    COST_TRACK --> PERF_TELEMETRY
    ERROR_MONITOR --> PERF_TELEMETRY
    
    %% Optimization Connections
    PREPROCESS --> CACHE_LAYER
    CACHE_LAYER --> DEDUP_CHECK
    VECTOR_PREP --> COMPRESSION
    BATCH_MANAGER --> PARALLEL_PROC
    
    %% Styling
    classDef input fill:#e1f5fe
    classDef processing fill:#f3e5f5
    classDef storage fill:#e8f5e8
    classDef quality fill:#fff3e0
    classDef performance fill:#fce4ec
    classDef optimization fill:#f1f8e9
    
    class RAW_DATA,CHUNK_QUEUE,BATCH_PROCESSOR input
    class PREPROCESS,TOKEN_LIMIT,BATCH_MANAGER,EMBED_REQUEST,CORTEX_API,VECTOR_VALIDATE,DIMENSION_CHECK processing
    class VECTOR_PREP,METADATA_LINK,EMBED_INSERT,EMBED_TABLE,INDEX_BUILD storage
    class SIMILARITY_CHECK,OUTLIER_DETECT,QUALITY_METRICS quality
    class LATENCY_TRACK,THROUGHPUT_MONITOR,COST_TRACK,ERROR_MONITOR,PERF_TELEMETRY performance
    class CACHE_LAYER,DEDUP_CHECK,COMPRESSION,PARALLEL_PROC optimization
```

## 4. Query Processing and LLM Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant API as Query API
    participant QP as Query Processor
    participant EMB as Embedding Service
    participant VS as Vector Search
    participant CTX as Context Builder
    participant LLM as LLM Service
    participant PP as Post Processor
    participant TEL as Telemetry
    participant DB as Snowflake DB
    
    Note over U,DB: Query Processing Flow
    
    U->>API: Submit Query
    API->>QP: Validate & Parse Query
    QP->>TEL: Log Query Start
    
    %% Query Embedding
    QP->>EMB: Generate Query Embedding
    EMB->>DB: CORTEX.EMBED_TEXT_768(query)
    DB-->>EMB: Query Vector
    EMB-->>QP: Query Embedding
    
    %% Semantic Search
    QP->>VS: Perform Vector Search
    VS->>DB: VECTOR_COSINE_SIMILARITY(query_vector, embeddings)
    DB-->>VS: Top-K Similar Chunks
    VS->>TEL: Log Search Metrics
    VS-->>QP: Ranked Results
    
    %% Context Building
    QP->>CTX: Build Context from Results
    CTX->>DB: Fetch Full Text Chunks
    DB-->>CTX: Document Chunks
    CTX-->>QP: Enhanced Context
    
    %% LLM Processing
    QP->>LLM: Generate Response
    LLM->>DB: CORTEX.COMPLETE(prompt + context)
    DB-->>LLM: Generated Response
    LLM->>TEL: Log LLM Metrics
    LLM-->>QP: Raw Response
    
    %% Post Processing
    QP->>PP: Post-process Response
    PP->>PP: Format & Validate
    PP-->>QP: Final Response
    
    %% Storage & Response
    QP->>DB: Store Query History
    QP->>TEL: Log Complete Transaction
    QP-->>API: Processed Response
    API-->>U: Final Answer + Metadata
    
    Note over TEL,DB: Telemetry Collection
    TEL->>DB: Store Performance Metrics
    TEL->>DB: Update Cost Tracking
```

## 5. Data Flow and Dependencies

```mermaid
graph LR
    subgraph "Data Sources"
        DOC_FILES[Document Files]
        USER_QUERIES[User Queries]
        CONFIG_DATA[Configuration Data]
    end
    
    subgraph "Core Processing Modules"
        UTILS[utils.py<br/>Connection Management]
        INGEST[ingest_loader.py<br/>Document Processing]
        EMBED[embed_generator.py<br/>Vector Generation]
        QUERY[cortex_query.py<br/>Query Processing]
        TELEMETRY[telemetry_task.py<br/>Monitoring]
        DASHBOARD[dashboard_plot.py<br/>Visualization]
    end
    
    subgraph "Snowflake Cortex Functions"
        EMBED_FUNC[CORTEX.EMBED_TEXT_768<br/>Vector Embeddings]
        COMPLETE_FUNC[CORTEX.COMPLETE<br/>LLM Completion]
        SIMILARITY_FUNC[VECTOR_COSINE_SIMILARITY<br/>Semantic Search]
    end
    
    subgraph "Data Storage Tables"
        RAW_TBL[(media_raw<br/>Document Storage)]
        EMBED_TBL[(media_embeddings<br/>Vector Storage)]
        QUERY_TBL[(query_history<br/>Query Logs)]
        TEL_TBL[(genai_telemetry<br/>Metrics Storage)]
    end
    
    subgraph "Configuration Files"
        ENV_CONFIG[config/creds.env<br/>Credentials]
        YAML_CONFIG[config/settings.yaml<br/>Settings]
        TOML_CONFIG[config/snowflake.toml<br/>Connection Config]
    end
    
    subgraph "External Interfaces"
        CLI[Command Line Interface]
        WEB_DASHBOARD[Web Dashboard]
        API_INTERFACE[API Interface]
    end
    
    %% Primary Data Flows
    DOC_FILES --> INGEST
    INGEST --> RAW_TBL
    RAW_TBL --> EMBED
    EMBED --> EMBED_FUNC
    EMBED_FUNC --> EMBED_TBL
    
    USER_QUERIES --> QUERY
    QUERY --> EMBED_FUNC
    QUERY --> SIMILARITY_FUNC
    SIMILARITY_FUNC --> EMBED_TBL
    QUERY --> COMPLETE_FUNC
    QUERY --> QUERY_TBL
    
    %% Configuration Dependencies
    ENV_CONFIG --> UTILS
    YAML_CONFIG --> UTILS
    TOML_CONFIG --> UTILS
    UTILS --> INGEST
    UTILS --> EMBED
    UTILS --> QUERY
    UTILS --> TELEMETRY
    
    %% Telemetry and Monitoring
    INGEST --> TELEMETRY
    EMBED --> TELEMETRY
    QUERY --> TELEMETRY
    TELEMETRY --> TEL_TBL
    TEL_TBL --> DASHBOARD
    
    %% User Interfaces
    CLI --> QUERY
    CLI --> INGEST
    CLI --> DASHBOARD
    WEB_DASHBOARD --> DASHBOARD
    API_INTERFACE --> QUERY
    
    %% Styling
    classDef source fill:#e3f2fd
    classDef module fill:#f3e5f5
    classDef cortex fill:#e8f5e8
    classDef storage fill:#fff3e0
    classDef config fill:#fafafa
    classDef interface fill:#f1f8e9
    
    class DOC_FILES,USER_QUERIES,CONFIG_DATA source
    class UTILS,INGEST,EMBED,QUERY,TELEMETRY,DASHBOARD module
    class EMBED_FUNC,COMPLETE_FUNC,SIMILARITY_FUNC cortex
    class RAW_TBL,EMBED_TBL,QUERY_TBL,TEL_TBL storage
    class ENV_CONFIG,YAML_CONFIG,TOML_CONFIG config
    class CLI,WEB_DASHBOARD,API_INTERFACE interface
```

## 6. Performance and Monitoring Architecture

```mermaid
graph TB
    subgraph "Application Layer"
        APP_SERVICES[Application Services]
        QUERY_ENGINE[Query Engine]
        EMBED_ENGINE[Embedding Engine]
        INGEST_ENGINE[Ingestion Engine]
    end
    
    subgraph "Telemetry Collection Layer"
        PERF_COLLECTOR[Performance Collector]
        COST_COLLECTOR[Cost Collector]
        ERROR_COLLECTOR[Error Collector]
        USAGE_COLLECTOR[Usage Collector]
    end
    
    subgraph "Metrics Processing"
        AGGREGATOR[Metrics Aggregator]
        PROCESSOR[Data Processor]
        CALCULATOR[Cost Calculator]
        ANALYZER[Performance Analyzer]
    end
    
    subgraph "Storage Layer"
        METRICS_DB[(genai_telemetry)]
        COST_DB[(cost_tracking)]
        PERF_DB[(performance_metrics)]
        ERROR_DB[(error_logs)]
    end
    
    subgraph "Analytics Engine"
        TREND_ANALYSIS[Trend Analysis]
        ANOMALY_DETECTION[Anomaly Detection]
        FORECAST[Usage Forecasting]
        OPTIMIZATION[Optimization Recommendations]
    end
    
    subgraph "Visualization Layer"
        REAL_TIME[Real-time Dashboard]
        HISTORICAL[Historical Reports]
        ALERTS[Alert System]
        EXECUTIVE[Executive Summary]
    end
    
    subgraph "External Integrations"
        SLACK_ALERTS[Slack Notifications]
        EMAIL_REPORTS[Email Reports]
        WEBHOOK_API[Webhook API]
        MONITORING_TOOLS[External Monitoring]
    end
    
    %% Data Flow Connections
    APP_SERVICES --> PERF_COLLECTOR
    QUERY_ENGINE --> PERF_COLLECTOR
    EMBED_ENGINE --> PERF_COLLECTOR
    INGEST_ENGINE --> PERF_COLLECTOR
    
    APP_SERVICES --> COST_COLLECTOR
    QUERY_ENGINE --> COST_COLLECTOR
    EMBED_ENGINE --> COST_COLLECTOR
    
    APP_SERVICES --> ERROR_COLLECTOR
    QUERY_ENGINE --> ERROR_COLLECTOR
    EMBED_ENGINE --> ERROR_COLLECTOR
    INGEST_ENGINE --> ERROR_COLLECTOR
    
    APP_SERVICES --> USAGE_COLLECTOR
    
    PERF_COLLECTOR --> AGGREGATOR
    COST_COLLECTOR --> AGGREGATOR
    ERROR_COLLECTOR --> AGGREGATOR
    USAGE_COLLECTOR --> AGGREGATOR
    
    AGGREGATOR --> PROCESSOR
    PROCESSOR --> CALCULATOR
    PROCESSOR --> ANALYZER
    
    CALCULATOR --> METRICS_DB
    ANALYZER --> PERF_DB
    ERROR_COLLECTOR --> ERROR_DB
    COST_COLLECTOR --> COST_DB
    
    METRICS_DB --> TREND_ANALYSIS
    PERF_DB --> TREND_ANALYSIS
    COST_DB --> TREND_ANALYSIS
    ERROR_DB --> ANOMALY_DETECTION
    
    TREND_ANALYSIS --> FORECAST
    ANOMALY_DETECTION --> OPTIMIZATION
    
    TREND_ANALYSIS --> REAL_TIME
    FORECAST --> HISTORICAL
    ANOMALY_DETECTION --> ALERTS
    OPTIMIZATION --> EXECUTIVE
    
    ALERTS --> SLACK_ALERTS
    HISTORICAL --> EMAIL_REPORTS
    REAL_TIME --> WEBHOOK_API
    EXECUTIVE --> MONITORING_TOOLS
    
    %% Styling
    classDef application fill:#e3f2fd
    classDef collection fill:#f3e5f5
    classDef processing fill:#fff3e0
    classDef storage fill:#e8f5e8
    classDef analytics fill:#f1f8e9
    classDef visualization fill:#fce4ec
    classDef integration fill:#e0f2f1
    
    class APP_SERVICES,QUERY_ENGINE,EMBED_ENGINE,INGEST_ENGINE application
    class PERF_COLLECTOR,COST_COLLECTOR,ERROR_COLLECTOR,USAGE_COLLECTOR collection
    class AGGREGATOR,PROCESSOR,CALCULATOR,ANALYZER processing
    class METRICS_DB,COST_DB,PERF_DB,ERROR_DB storage
    class TREND_ANALYSIS,ANOMALY_DETECTION,FORECAST,OPTIMIZATION analytics
    class REAL_TIME,HISTORICAL,ALERTS,EXECUTIVE visualization
    class SLACK_ALERTS,EMAIL_REPORTS,WEBHOOK_API,MONITORING_TOOLS integration
```

## 7. Deployment and CI/CD Architecture

```mermaid
graph TD
    subgraph "Source Control"
        GITHUB[GitHub Repository]
        FEATURE_BRANCH[Feature Branches]
        MAIN_BRANCH[Main Branch]
        RELEASE_TAGS[Release Tags]
    end
    
    subgraph "GitHub Actions Workflow"
        TRIGGER[Workflow Trigger]
        VALIDATION[Code Validation]
        TESTING[Automated Testing]
        SECURITY[Security Scanning]
        BUILD[Build Process]
        DEPLOY_STAGING[Deploy to Staging]
        INTEGRATION_TESTS[Integration Tests]
        DEPLOY_PROD[Deploy to Production]
    end
    
    subgraph "Validation Pipeline"
        LINT[Code Linting]
        FORMAT[Code Formatting]
        TYPE_CHECK[Type Checking]
        SQL_VALIDATE[SQL Validation]
        CONFIG_VALIDATE[Config Validation]
    end
    
    subgraph "Testing Pipeline"
        UNIT_TESTS[Unit Tests]
        INTEGRATION_TESTS_2[Integration Tests]
        PERFORMANCE_TESTS[Performance Tests]
        SECURITY_TESTS[Security Tests]
        CORTEX_TESTS[Cortex Function Tests]
    end
    
    subgraph "Snowflake Deployment"
        SF_AUTH[Snowflake Authentication]
        SCHEMA_DEPLOY[Schema Deployment]
        FUNCTION_DEPLOY[Function Deployment]
        DATA_SEED[Data Seeding]
        PERMISSION_SETUP[Permission Setup]
    end
    
    subgraph "Environment Management"
        DEV_ENV[Development Environment]
        STAGING_ENV[Staging Environment]
        PROD_ENV[Production Environment]
        MONITORING_ENV[Monitoring Environment]
    end
    
    subgraph "Monitoring and Alerts"
        DEPLOY_MONITOR[Deployment Monitoring]
        HEALTH_CHECKS[Health Checks]
        ROLLBACK[Automated Rollback]
        NOTIFICATION[Deployment Notifications]
    end
    
    %% Workflow Connections
    GITHUB --> TRIGGER
    FEATURE_BRANCH --> TRIGGER
    MAIN_BRANCH --> TRIGGER
    RELEASE_TAGS --> TRIGGER
    
    TRIGGER --> VALIDATION
    VALIDATION --> TESTING
    TESTING --> SECURITY
    SECURITY --> BUILD
    BUILD --> DEPLOY_STAGING
    DEPLOY_STAGING --> INTEGRATION_TESTS
    INTEGRATION_TESTS --> DEPLOY_PROD
    
    %% Validation Connections
    VALIDATION --> LINT
    VALIDATION --> FORMAT
    VALIDATION --> TYPE_CHECK
    VALIDATION --> SQL_VALIDATE
    VALIDATION --> CONFIG_VALIDATE
    
    %% Testing Connections
    TESTING --> UNIT_TESTS
    TESTING --> INTEGRATION_TESTS_2
    TESTING --> PERFORMANCE_TESTS
    TESTING --> SECURITY_TESTS
    TESTING --> CORTEX_TESTS
    
    %% Deployment Connections
    BUILD --> SF_AUTH
    SF_AUTH --> SCHEMA_DEPLOY
    SCHEMA_DEPLOY --> FUNCTION_DEPLOY
    FUNCTION_DEPLOY --> DATA_SEED
    DATA_SEED --> PERMISSION_SETUP
    
    %% Environment Connections
    DEPLOY_STAGING --> DEV_ENV
    DEPLOY_STAGING --> STAGING_ENV
    DEPLOY_PROD --> PROD_ENV
    DEPLOY_PROD --> MONITORING_ENV
    
    %% Monitoring Connections
    DEPLOY_PROD --> DEPLOY_MONITOR
    DEPLOY_MONITOR --> HEALTH_CHECKS
    HEALTH_CHECKS --> ROLLBACK
    ROLLBACK --> NOTIFICATION
    
    %% Styling
    classDef source fill:#e3f2fd
    classDef workflow fill:#f3e5f5
    classDef validation fill:#fff3e0
    classDef testing fill:#e8f5e8
    classDef deployment fill:#f1f8e9
    classDef environment fill:#fce4ec
    classDef monitoring fill:#e0f2f1
    
    class GITHUB,FEATURE_BRANCH,MAIN_BRANCH,RELEASE_TAGS source
    class TRIGGER,VALIDATION,TESTING,SECURITY,BUILD,DEPLOY_STAGING,INTEGRATION_TESTS,DEPLOY_PROD workflow
    class LINT,FORMAT,TYPE_CHECK,SQL_VALIDATE,CONFIG_VALIDATE validation
    class UNIT_TESTS,INTEGRATION_TESTS_2,PERFORMANCE_TESTS,SECURITY_TESTS,CORTEX_TESTS testing
    class SF_AUTH,SCHEMA_DEPLOY,FUNCTION_DEPLOY,DATA_SEED,PERMISSION_SETUP deployment
    class DEV_ENV,STAGING_ENV,PROD_ENV,MONITORING_ENV environment
    class DEPLOY_MONITOR,HEALTH_CHECKS,ROLLBACK,NOTIFICATION monitoring
```

## 8. Security and Access Control Architecture

```mermaid
graph TB
    subgraph "External Access Layer"
        USERS[End Users]
        ADMINS[System Administrators]
        DEVS[Developers]
        API_CLIENTS[API Clients]
    end
    
    subgraph "Authentication Layer"
        AUTH_GATEWAY[Authentication Gateway]
        SSO[Single Sign-On]
        API_KEYS[API Key Management]
        MFA[Multi-Factor Authentication]
    end
    
    subgraph "Authorization Layer"
        RBAC[Role-Based Access Control]
        POLICY_ENGINE[Policy Engine]
        PERMISSION_CHECK[Permission Validation]
        RESOURCE_ACCESS[Resource Access Control]
    end
    
    subgraph "Application Security"
        INPUT_VAL[Input Validation]
        SQL_INJECT[SQL Injection Prevention]
        RATE_LIMIT[Rate Limiting]
        CONTENT_FILTER[Content Filtering]
    end
    
    subgraph "Snowflake Security"
        SF_RBAC[Snowflake RBAC]
        NETWORK_POLICY[Network Policies]
        ENCRYPTION[Data Encryption]
        AUDIT_LOG[Audit Logging]
    end
    
    subgraph "Data Protection"
        PII_DETECT[PII Detection]
        DATA_MASK[Data Masking]
        RETENTION[Data Retention]
        BACKUP[Secure Backup]
    end
    
    subgraph "Monitoring and Compliance"
        SECURITY_MONITOR[Security Monitoring]
        THREAT_DETECT[Threat Detection]
        COMPLIANCE_CHECK[Compliance Validation]
        INCIDENT_RESPONSE[Incident Response]
    end
    
    %% Access Flow
    USERS --> AUTH_GATEWAY
    ADMINS --> AUTH_GATEWAY
    DEVS --> AUTH_GATEWAY
    API_CLIENTS --> API_KEYS
    
    AUTH_GATEWAY --> SSO
    AUTH_GATEWAY --> MFA
    API_KEYS --> AUTH_GATEWAY
    
    SSO --> RBAC
    MFA --> RBAC
    RBAC --> POLICY_ENGINE
    POLICY_ENGINE --> PERMISSION_CHECK
    PERMISSION_CHECK --> RESOURCE_ACCESS
    
    %% Security Processing
    RESOURCE_ACCESS --> INPUT_VAL
    INPUT_VAL --> SQL_INJECT
    SQL_INJECT --> RATE_LIMIT
    RATE_LIMIT --> CONTENT_FILTER
    
    %% Snowflake Security
    CONTENT_FILTER --> SF_RBAC
    SF_RBAC --> NETWORK_POLICY
    NETWORK_POLICY --> ENCRYPTION
    ENCRYPTION --> AUDIT_LOG
    
    %% Data Protection
    ENCRYPTION --> PII_DETECT
    PII_DETECT --> DATA_MASK
    DATA_MASK --> RETENTION
    RETENTION --> BACKUP
    
    %% Monitoring
    AUDIT_LOG --> SECURITY_MONITOR
    SECURITY_MONITOR --> THREAT_DETECT
    THREAT_DETECT --> COMPLIANCE_CHECK
    COMPLIANCE_CHECK --> INCIDENT_RESPONSE
    
    %% Styling
    classDef access fill:#e3f2fd
    classDef auth fill:#f3e5f5
    classDef authz fill:#fff3e0
    classDef security fill:#e8f5e8
    classDef snowflake fill:#f1f8e9
    classDef protection fill:#fce4ec
    classDef monitoring fill:#e0f2f1
    
    class USERS,ADMINS,DEVS,API_CLIENTS access
    class AUTH_GATEWAY,SSO,API_KEYS,MFA auth
    class RBAC,POLICY_ENGINE,PERMISSION_CHECK,RESOURCE_ACCESS authz
    class INPUT_VAL,SQL_INJECT,RATE_LIMIT,CONTENT_FILTER security
    class SF_RBAC,NETWORK_POLICY,ENCRYPTION,AUDIT_LOG snowflake
    class PII_DETECT,DATA_MASK,RETENTION,BACKUP protection
    class SECURITY_MONITOR,THREAT_DETECT,COMPLIANCE_CHECK,INCIDENT_RESPONSE monitoring
```

## Implementation Notes

1. **Scalability**: The architecture supports horizontal scaling through Snowflake's compute resources
2. **Reliability**: Built-in retry mechanisms and error handling ensure robust operation
3. **Performance**: Optimized data flow minimizes latency and maximizes throughput
4. **Security**: Multi-layered security approach protects data and ensures compliance
5. **Monitoring**: Comprehensive telemetry provides visibility into system performance
6. **Deployment**: Automated CI/CD ensures reliable and consistent deployments

## Next Steps

1. Review and validate architectural decisions
2. Implement monitoring and alerting systems
3. Set up automated testing and deployment pipelines
4. Establish security policies and access controls
5. Create operational runbooks and documentation
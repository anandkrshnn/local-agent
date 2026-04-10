# Architecture Specification: Local Agent Security Airlock

This document details the "Security Airlock" pattern implemented via the Local Permission Broker (LPB).

## 1. High-Level Flow (Mermaid)

```mermaid
graph TD
    subgraph "User Interface Layer"
        UI[Web Dashboard / CLI]
    end

    subgraph "Intelligence Layer (Untrusted)"
        LLM[AI Model via Ollama]
        ReAct[ReAct Execution Loop]
    end

    subgraph "Security Layer (Trusted)"
        LPB{Local Permission Broker}
        TokenGen[Token Generator]
        Audit[Audit Trail Store]
    end

    subgraph "Execution Layer (Sandboxed)"
        Executor[Tool Executor]
        Sandbox[Filesystem Sandbox]
        Memory[DuckDB Semantic Memory]
    end

    UI -->|Query| LLM
    LLM -->|Thought| ReAct
    ReAct -->|Request Tool Call| LPB
    
    LPB -->|Policy Check| LPB
    LPB -->|Learning Check| LPB
    
    LPB -- Manual Decision --> UI
    UI -- Manual Approval --> LPB
    
    LPB -->|Create 60s Token| TokenGen
    TokenGen -->|Return Token| ReAct
    ReAct -->|Execute with Token| Executor
    
    Executor -->|Verify Token & Consume| LPB
    Executor -->|Log Event| Audit
    Executor -->|Perform IO| Sandbox
    Executor -->|Query Vecs| Memory
    
    Sandbox -->|Result| ReAct
    Memory -->|Recall| ReAct
    ReAct -->|Final Answer| UI

    style LPB fill:#f96,stroke:#333,stroke-width:4px
    style Sandbox fill:#eee,stroke:#999,stroke-style:dashed
```

## 2. Component Breakdown

### 2.1 Local Permission Broker (LPB)
- **Role**: The centralized policy decision point.
- **Logic**: Implements a sliding scale of trust.
- **Auto-Learning**: Monitors the `audit_log` for repeated (8+) identical Tool + Resource patterns. If found within the sliding 24h window, it elevates the pattern to "Trusted."

### 2.2 Token-Based Protocol
- **Specification**: HMAC-SHA256 signed JSON payload.
- **Payload Structure**:
  ```json
  {
    "token_id": "uuid-v4",
    "intent": "write_file",
    "resource": "sandbox/notes.txt",
    "iat": 1712741400,
    "exp": 1712741460 
  }
  ```
- **Consumption Requirement**: The Token Executor *must* call `broker.validate_token()` which deletes the token from memory (making it single-use) before the actual I/O operation occurs.

### 2.3 Semantic Memory Stack
- **Engine**: DuckDB.
- **Index**: HNSW (Hierarchical Navigable Small World) for fast vector retrieval.
- **Embeddings**: `all-MiniLM-L6-v2` (384 dimensions).

### 2.4 Hallucination Guard
- **Mechanism**: A static whitelist of `VALID_TOOLS`.
- **Behavior**: If the LLM generates a tool call not present in the registry, the orchestrator returns a system-level error to the model's context, forcing a "Think" step to find an alternative.

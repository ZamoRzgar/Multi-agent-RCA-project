# Knowledge Graph Schema Design

**Purpose**: Define the structure of the knowledge graph for RCA  
**Date**: December 5, 2025  
**Status**: Design Phase

---

## 🎯 Overview

The knowledge graph stores historical incidents, events, entities, and their relationships to support:
1. **Similar incident retrieval** - Find past incidents with similar patterns
2. **Causal path discovery** - Identify cause-effect chains
3. **Entity context** - Understand entity roles and relationships
4. **Pattern recognition** - Detect recurring failure patterns

---

## 📊 Node Types

### 1. Incident Node

**Purpose**: Represents a failure case or anomaly

**Properties**:
```python
{
    "id": str,              # Unique identifier (e.g., "HDFS_001")
    "timestamp": datetime,  # When incident occurred
    "dataset": str,         # Source dataset (HDFS, BGL, Hadoop)
    "label": str,          # Failure label (if available)
    "severity": str,       # INFO, WARN, ERROR, CRITICAL
    "duration": int,       # Duration in seconds
    "resolved": bool,      # Whether resolved
    "root_cause": str,     # Known root cause (if labeled)
    "description": str     # Human-readable description
}
```

**Example**:
```cypher
CREATE (i:Incident {
    id: 'HDFS_001',
    timestamp: datetime('2025-12-05T10:00:00'),
    dataset: 'HDFS',
    label: 'Block Replication Failure',
    severity: 'ERROR',
    duration: 300,
    resolved: true,
    root_cause: 'DataNode disk full',
    description: 'Block replication failed due to insufficient disk space'
})
```

---

### 2. Event Node

**Purpose**: Represents a single log event

**Properties**:
```python
{
    "id": str,              # Unique identifier
    "timestamp": datetime,  # Event timestamp
    "component": str,       # Component name (e.g., "DataNode")
    "action": str,          # Action performed (e.g., "replication_failed")
    "severity": str,        # INFO, WARN, ERROR
    "message": str,         # Full log message
    "template_id": str,     # Associated template ID
    "parameters": dict      # Extracted parameters
}
```

**Example**:
```cypher
CREATE (e:Event {
    id: 'EVT_001',
    timestamp: datetime('2025-12-05T10:00:00'),
    component: 'DataNode',
    action: 'block_replication_failed',
    severity: 'ERROR',
    message: 'Block blk_123 replication failed to /10.0.1.5',
    template_id: 'TPL_001',
    parameters: {block_id: 'blk_123', target_ip: '/10.0.1.5'}
})
```

---

### 3. Entity Node

**Purpose**: Represents system entities (services, hosts, components, etc.)

**Properties**:
```python
{
    "id": str,          # Unique identifier
    "type": str,        # service, host, component, user, file, ip, block
    "name": str,        # Entity name
    "context": str,     # Additional context
    "properties": dict  # Type-specific properties
}
```

**Subtypes**:
- **Service**: `{port: int, protocol: str}`
- **Host**: `{ip: str, hostname: str, datacenter: str}`
- **Component**: `{version: str, role: str}`
- **Block**: `{size: int, replication_factor: int}`

**Example**:
```cypher
CREATE (e:Entity:Host {
    id: 'HOST_001',
    type: 'host',
    name: '/10.0.1.5',
    context: 'DataNode server',
    properties: {
        ip: '10.0.1.5',
        hostname: 'datanode-05',
        datacenter: 'DC1'
    }
})
```

---

### 4. Error Node

**Purpose**: Represents error messages and exceptions

**Properties**:
```python
{
    "id": str,          # Unique identifier
    "error_type": str,  # Error classification
    "message": str,     # Error message
    "component": str,   # Component that reported error
    "stack_trace": str, # Stack trace (if available)
    "frequency": int    # How often this error occurs
}
```

**Example**:
```cypher
CREATE (err:Error {
    id: 'ERR_001',
    error_type: 'DiskFullException',
    message: 'No space left on device',
    component: 'DataNode',
    stack_trace: null,
    frequency: 15
})
```

---

### 5. Template Node

**Purpose**: Represents log templates (patterns)

**Properties**:
```python
{
    "id": str,          # Unique identifier
    "pattern": str,     # Template pattern with wildcards
    "dataset": str,     # Source dataset
    "frequency": int,   # How often this template appears
    "parameters": list  # List of parameter names
}
```

**Example**:
```cypher
CREATE (t:Template {
    id: 'TPL_001',
    pattern: 'Block <*> replication failed to <*>',
    dataset: 'HDFS',
    frequency: 150,
    parameters: ['block_id', 'target_ip']
})
```

---

### 6. RootCause Node

**Purpose**: Represents known root causes

**Properties**:
```python
{
    "id": str,              # Unique identifier
    "description": str,     # Root cause description
    "category": str,        # hardware, software, network, config, resource
    "confidence": float,    # Confidence score (0-1)
    "resolution": str,      # How to resolve
    "frequency": int        # How often this root cause occurs
}
```

**Example**:
```cypher
CREATE (rc:RootCause {
    id: 'RC_001',
    description: 'Disk space exhausted on DataNode',
    category: 'resource',
    confidence: 0.95,
    resolution: 'Clear disk space or add storage',
    frequency: 12
})
```

---

## 🔗 Relationship Types

### 1. CONTAINS

**Direction**: Incident → Event  
**Purpose**: Incident contains multiple events  
**Properties**: `{sequence: int}` (order of events)

```cypher
(i:Incident)-[:CONTAINS {sequence: 1}]->(e:Event)
```

---

### 2. INVOLVES

**Direction**: Event → Entity  
**Purpose**: Event involves an entity  
**Properties**: `{role: str}` (source, target, affected)

```cypher
(e:Event)-[:INVOLVES {role: 'source'}]->(entity:Entity)
```

---

### 3. REPORTS

**Direction**: Event → Error  
**Purpose**: Event reports an error  
**Properties**: None

```cypher
(e:Event)-[:REPORTS]->(err:Error)
```

---

### 4. CAUSES

**Direction**: Event → Event  
**Purpose**: Causal relationship between events  
**Properties**: `{confidence: float, delay: int}` (confidence score, time delay in seconds)

```cypher
(e1:Event)-[:CAUSES {confidence: 0.8, delay: 5}]->(e2:Event)
```

---

### 5. PRECEDES

**Direction**: Event → Event  
**Purpose**: Temporal relationship (happens before)  
**Properties**: `{delay: int}` (time difference in seconds)

```cypher
(e1:Event)-[:PRECEDES {delay: 10}]->(e2:Event)
```

---

### 6. SIMILAR_TO

**Direction**: Incident ↔ Incident  
**Purpose**: Similarity between incidents  
**Properties**: `{similarity: float, method: str}` (similarity score, method used)

```cypher
(i1:Incident)-[:SIMILAR_TO {similarity: 0.85, method: 'cosine'}]-(i2:Incident)
```

---

### 7. HAS_ROOT_CAUSE

**Direction**: Incident → RootCause  
**Purpose**: Incident has a known root cause  
**Properties**: `{confidence: float}` (confidence in diagnosis)

```cypher
(i:Incident)-[:HAS_ROOT_CAUSE {confidence: 0.9}]->(rc:RootCause)
```

---

### 8. MATCHES

**Direction**: Event → Template  
**Purpose**: Event matches a template  
**Properties**: None

```cypher
(e:Event)-[:MATCHES]->(t:Template)
```

---

## 📐 Schema Visualization

```
                    ┌─────────────┐
                    │  Incident   │
                    └──────┬──────┘
                           │
                ┌──────────┼──────────┐
                │          │          │
         [CONTAINS]  [SIMILAR_TO] [HAS_ROOT_CAUSE]
                │          │          │
                ▼          ▼          ▼
         ┌─────────┐ ┌─────────┐ ┌──────────┐
         │  Event  │ │Incident │ │RootCause │
         └────┬────┘ └─────────┘ └──────────┘
              │
    ┌─────────┼─────────┬─────────┐
    │         │         │         │
[INVOLVES] [REPORTS] [CAUSES] [MATCHES]
    │         │         │         │
    ▼         ▼         ▼         ▼
┌────────┐ ┌───────┐ ┌─────┐ ┌─────────┐
│ Entity │ │ Error │ │Event│ │Template │
└────────┘ └───────┘ └─────┘ └─────────┘
```

---

## 🔍 Example Queries

### Query 1: Find Similar Incidents

```cypher
// Find incidents similar to a given incident
MATCH (i1:Incident {id: 'HDFS_001'})-[s:SIMILAR_TO]-(i2:Incident)
WHERE s.similarity > 0.7
RETURN i2
ORDER BY s.similarity DESC
LIMIT 10
```

---

### Query 2: Find Causal Chains

```cypher
// Find causal chains leading to an error
MATCH path = (e1:Event)-[:CAUSES*1..5]->(e2:Event)-[:REPORTS]->(err:Error)
WHERE err.error_type = 'DiskFullException'
RETURN path
ORDER BY length(path) DESC
LIMIT 5
```

---

### Query 3: Find Entities Involved in Failures

```cypher
// Find entities frequently involved in failures
MATCH (i:Incident {severity: 'ERROR'})-[:CONTAINS]->(e:Event)-[:INVOLVES]->(entity:Entity)
RETURN entity.name, entity.type, count(*) AS failure_count
ORDER BY failure_count DESC
LIMIT 10
```

---

### Query 4: Find Common Root Causes

```cypher
// Find most common root causes
MATCH (i:Incident)-[:HAS_ROOT_CAUSE]->(rc:RootCause)
RETURN rc.description, rc.category, count(*) AS frequency
ORDER BY frequency DESC
LIMIT 10
```

---

### Query 5: Find Temporal Patterns

```cypher
// Find events that typically precede errors
MATCH (e1:Event)-[:PRECEDES]->(e2:Event)-[:REPORTS]->(err:Error)
WHERE e1.component <> e2.component
RETURN e1.component, e2.component, err.error_type, count(*) AS frequency
ORDER BY frequency DESC
LIMIT 10
```

---

## 🏗️ Schema Creation Script

```cypher
// Create constraints for uniqueness
CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT error_id IF NOT EXISTS FOR (e:Error) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT template_id IF NOT EXISTS FOR (t:Template) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT root_cause_id IF NOT EXISTS FOR (rc:RootCause) REQUIRE rc.id IS UNIQUE;

// Create indexes for performance
CREATE INDEX incident_timestamp IF NOT EXISTS FOR (i:Incident) ON (i.timestamp);
CREATE INDEX incident_dataset IF NOT EXISTS FOR (i:Incident) ON (i.dataset);
CREATE INDEX event_timestamp IF NOT EXISTS FOR (e:Event) ON (e.timestamp);
CREATE INDEX event_component IF NOT EXISTS FOR (e:Event) ON (e.component);
CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name);
CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type);
CREATE INDEX error_type IF NOT EXISTS FOR (e:Error) ON (e.error_type);
CREATE INDEX template_pattern IF NOT EXISTS FOR (t:Template) ON (t.pattern);
```

---

## 📊 Sample Data Population

```cypher
// Create sample incident
CREATE (i:Incident {
    id: 'HDFS_001',
    timestamp: datetime('2025-12-05T10:00:00'),
    dataset: 'HDFS',
    label: 'Block Replication Failure',
    severity: 'ERROR',
    duration: 300,
    resolved: true,
    root_cause: 'DataNode disk full'
})

// Create events
CREATE (e1:Event {
    id: 'EVT_001',
    timestamp: datetime('2025-12-05T10:00:00'),
    component: 'DataNode',
    action: 'disk_check',
    severity: 'WARN',
    message: 'Disk usage at 95%'
})

CREATE (e2:Event {
    id: 'EVT_002',
    timestamp: datetime('2025-12-05T10:00:05'),
    component: 'DataNode',
    action: 'replication_failed',
    severity: 'ERROR',
    message: 'Block replication failed: No space left'
})

// Create entity
CREATE (host:Entity:Host {
    id: 'HOST_001',
    type: 'host',
    name: '/10.0.1.5',
    context: 'DataNode server'
})

// Create error
CREATE (err:Error {
    id: 'ERR_001',
    error_type: 'DiskFullException',
    message: 'No space left on device',
    component: 'DataNode'
})

// Create root cause
CREATE (rc:RootCause {
    id: 'RC_001',
    description: 'Disk space exhausted',
    category: 'resource',
    confidence: 0.95
})

// Create relationships
CREATE (i)-[:CONTAINS {sequence: 1}]->(e1)
CREATE (i)-[:CONTAINS {sequence: 2}]->(e2)
CREATE (e1)-[:CAUSES {confidence: 0.8, delay: 5}]->(e2)
CREATE (e1)-[:PRECEDES {delay: 5}]->(e2)
CREATE (e2)-[:INVOLVES {role: 'source'}]->(host)
CREATE (e2)-[:REPORTS]->(err)
CREATE (i)-[:HAS_ROOT_CAUSE {confidence: 0.9}]->(rc)
```

---

## 🎯 Next Steps

1. ✅ Schema designed
2. ⏳ Create schema in Neo4j
3. ⏳ Implement KGRetrievalAgent
4. ⏳ Populate with loghub data
5. ⏳ Test queries

---

**Status**: Schema design complete  
**Next**: Implement KGRetrievalAgent class  
**File**: `src/agents/kg_retrieval.py`

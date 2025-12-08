# Week 2 Start - KG Retrieval Agent

**Date**: December 5, 2025  
**Status**: Ready to Begin  
**Current Task**: Install Neo4j and implement KG Retrieval Agent

---

## 📚 Documentation Created

I've created comprehensive guides for Week 2, Day 1-2:

### 1. **Neo4j Setup Guide**
**File**: `docs/setup/NEO4J_SETUP.md`

**Contents**:
- 3 installation options (Desktop, Community, Docker)
- Configuration instructions
- Python driver installation
- Connection testing
- Troubleshooting guide

**Recommendation**: Use **Docker** (easiest and cleanest)

---

### 2. **KG Schema Design**
**File**: `docs/implementation/kg_schema.md`

**Contents**:
- 6 node types (Incident, Event, Entity, Error, Template, RootCause)
- 8 relationship types (CONTAINS, INVOLVES, CAUSES, etc.)
- Schema visualization
- Example queries
- Sample data

---

### 3. **KG Retrieval Implementation Guide**
**File**: `docs/implementation/kg_retrieval_guide.md`

**Contents**:
- Complete class structure
- 4 main query methods
- Test scripts
- Expected outputs

---

## 🚀 Next Steps (Choose Your Path)

### Option A: Quick Start with Docker (Recommended)

**Time**: ~30 minutes

```bash
# 1. Install Neo4j with Docker
docker pull neo4j:latest

docker run \
    --name neo4j-rca \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/rca_password_2025 \
    -e NEO4J_PLUGINS='["apoc"]' \
    -v $HOME/neo4j/data:/data \
    -v $HOME/neo4j/logs:/logs \
    -d \
    neo4j:latest

# 2. Wait for Neo4j to start (~30 seconds)
sleep 30

# 3. Check if running
docker ps | grep neo4j

# 4. Install Python driver
conda activate multimodel-rca
pip install neo4j py2neo networkx

# 5. Test connection
python tests/test_neo4j_connection.py
```

---

### Option B: Neo4j Desktop (GUI)

**Time**: ~45 minutes

1. Download from https://neo4j.com/download/
2. Install and create project
3. Create database "rca-knowledge-graph"
4. Set password
5. Start database
6. Install Python driver
7. Test connection

---

### Option C: System Installation

**Time**: ~45 minutes

```bash
# Add repository
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list

# Install
sudo apt-get update
sudo apt-get install neo4j

# Configure and start
sudo neo4j-admin set-initial-password rca_password_2025
sudo systemctl start neo4j
sudo systemctl enable neo4j

# Install Python driver
conda activate multimodel-rca
pip install neo4j py2neo networkx

# Test connection
python tests/test_neo4j_connection.py
```

---

## 📋 Implementation Checklist

### Phase 1: Setup (30-45 min)
- [ ] Choose installation method
- [ ] Install Neo4j
- [ ] Verify Neo4j is running
- [ ] Install Python driver
- [ ] Test connection
- [ ] Create schema (constraints and indexes)

### Phase 2: Implementation (3-4 hours)
- [ ] Create `src/agents/kg_retrieval.py`
- [ ] Implement `__init__()` and connection
- [ ] Implement `process()` method
- [ ] Implement `query_similar_incidents()`
- [ ] Implement `find_causal_paths()`
- [ ] Implement `get_entity_context()`
- [ ] Implement `get_common_patterns()`
- [ ] Implement `_execute_query()` helper

### Phase 3: Testing (1-2 hours)
- [ ] Create test files
- [ ] Test connection
- [ ] Test each query method
- [ ] Populate sample data
- [ ] Test with real log parser output
- [ ] Validate results

---

## 🎯 Quick Start Commands

### If you choose Docker (recommended):

```bash
# Terminal 1: Start Neo4j
cd ~/projects/log
docker run --name neo4j-rca -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/rca_password_2025 \
    -e NEO4J_PLUGINS='["apoc"]' \
    -v $HOME/neo4j/data:/data -d neo4j:latest

# Wait 30 seconds, then check
docker logs neo4j-rca

# Terminal 2: Install Python driver
conda activate multimodel-rca
pip install neo4j py2neo networkx

# Terminal 3: Open Neo4j Browser
# Visit: http://localhost:7474
# Username: neo4j
# Password: rca_password_2025
```

---

## 📊 Time Estimates

| Task | Time | Status |
|------|------|--------|
| **Neo4j Installation** | 30-45 min | ⏳ Pending |
| **Schema Creation** | 15 min | ⏳ Pending |
| **KGRetrievalAgent Implementation** | 3-4 hours | ⏳ Pending |
| **Testing** | 1-2 hours | ⏳ Pending |
| **Total** | 5-7 hours | ⏳ Pending |

---

## 💡 Tips

### For Docker Users:
- Data persists in `$HOME/neo4j/data`
- Logs in `$HOME/neo4j/logs`
- Stop: `docker stop neo4j-rca`
- Start: `docker start neo4j-rca`
- Remove: `docker rm -f neo4j-rca` (careful - deletes data!)

### For All Users:
- **Neo4j Browser**: http://localhost:7474
- **Bolt Port**: 7687 (for Python driver)
- **HTTP Port**: 7474 (for browser)
- **Default Username**: neo4j
- **Password**: Set during installation

### Connection String:
```python
uri = "bolt://localhost:7687"
username = "neo4j"
password = "rca_password_2025"  # Or whatever you set
```

---

## 🔍 Verification Steps

After installation, verify everything works:

### 1. Check Neo4j is Running
```bash
# Docker
docker ps | grep neo4j

# System install
sudo systemctl status neo4j
```

### 2. Access Browser
- Open: http://localhost:7474
- Login with credentials
- Run: `RETURN 'Hello, Neo4j!' AS message`
- Should see: "Hello, Neo4j!"

### 3. Test Python Connection
```bash
cd ~/projects/log
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'rca_password_2025'))
driver.verify_connectivity()
print('✓ Connected!')
driver.close()
"
```

---

## 📁 Files to Create

### 1. Connection Test
**File**: `tests/test_neo4j_connection.py`
```python
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "rca_password_2025"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
driver.verify_connectivity()
print("✓ Connected to Neo4j successfully!")
driver.close()
```

### 2. Schema Creation
**File**: `scripts/create_kg_schema.py`
```python
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "rca_password_2025"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

with driver.session() as session:
    # Create constraints
    session.run("CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE")
    session.run("CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE")
    # ... more constraints
    
    # Create indexes
    session.run("CREATE INDEX incident_timestamp IF NOT EXISTS FOR (i:Incident) ON (i.timestamp)")
    session.run("CREATE INDEX event_component IF NOT EXISTS FOR (e:Event) ON (e.component)")
    # ... more indexes
    
    print("✓ Schema created successfully!")

driver.close()
```

### 3. KG Retrieval Agent
**File**: `src/agents/kg_retrieval.py`
(See implementation guide for full code)

---

## 🎯 Success Criteria

By end of Day 1-2, you should have:
- ✅ Neo4j installed and running
- ✅ Python driver working
- ✅ Schema created
- ✅ KGRetrievalAgent implemented
- ✅ Basic tests passing
- ✅ Ready for Day 3 (RCA Reasoners)

---

## 🚦 Decision Point

**Which installation method do you want to use?**

1. **Docker** (recommended) - Easiest, cleanest
2. **Neo4j Desktop** - GUI, good for exploration
3. **System Install** - Production-ready

Let me know and I'll help you get started! 🚀

---

**Status**: Ready to begin  
**Estimated Time**: 5-7 hours total  
**Next**: Choose installation method and proceed

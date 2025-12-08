# Neo4j Setup - Next Steps

**Status**: Neo4j installed ✅  
**Current Step**: Verify connection and create schema

---

## 🔧 Step-by-Step Instructions

### Step 0: how to run Neo4j: 

./neo4j-desktop.AppImage --no-sandbox

### Step 1: Update Password in Configuration Files

You need to update your Neo4j password in 3 files:

#### File 1: `tests/test_neo4j_connection.py`
```python
# Line 12
PASSWORD = "your_actual_password"  # Replace with your Neo4j password
```

#### File 2: `scripts/create_kg_schema.py`
```python
# Line 12
PASSWORD = "your_actual_password"  # Replace with your Neo4j password
```

#### File 3: `config/neo4j_config.yaml`
```yaml
# Line 5
password: "your_actual_password"  # Replace with your Neo4j password
```

---

### Step 2: Test Neo4j Connection

```bash
cd ~/projects/log
conda activate multimodel-rca
python tests/test_neo4j_connection.py
```

**Expected Output:**
```
Connecting to Neo4j at bolt://localhost:7687...
✓ Connected to Neo4j successfully!
✓ Query result: Hello, Neo4j!
✓ Neo4j Graph Database version: 5.x.x
✓ Connection closed successfully!

============================================================
✓ Neo4j is ready to use!
============================================================
```

**If you get an error:**
- Check if Neo4j is running
- Verify the password is correct
- Ensure port 7687 is accessible

---

### Step 3: Create Knowledge Graph Schema

```bash
python scripts/create_kg_schema.py
```

**Expected Output:**
```
Creating Knowledge Graph schema...
============================================================

1. Creating constraints...
  ✓ Created constraint: incident_id
  ✓ Created constraint: event_id
  ✓ Created constraint: entity_id
  ✓ Created constraint: error_id
  ✓ Created constraint: template_id
  ✓ Created constraint: root_cause_id

2. Creating indexes...
  ✓ Created index: incident_timestamp
  ✓ Created index: incident_dataset
  ✓ Created index: event_timestamp
  ✓ Created index: event_component
  ✓ Created index: entity_name
  ✓ Created index: entity_type
  ✓ Created index: error_type
  ✓ Created index: template_pattern

3. Verifying schema...
  ✓ Total constraints: 6
  ✓ Total indexes: 10+

============================================================
✓ Schema created successfully!
============================================================
```

---

### Step 4: Verify Schema in Neo4j Browser (Optional)

1. Open Neo4j Browser: http://localhost:7474
2. Login with your credentials
3. Run these queries:

```cypher
// Show all constraints
SHOW CONSTRAINTS

// Show all indexes
SHOW INDEXES

// Check database is empty (should return 0)
MATCH (n) RETURN count(n) AS node_count
```

---

## 📋 Checklist

- [ ] Updated password in `tests/test_neo4j_connection.py`
- [ ] Updated password in `scripts/create_kg_schema.py`
- [ ] Updated password in `config/neo4j_config.yaml`
- [ ] Ran connection test successfully
- [ ] Created schema successfully
- [ ] Verified schema in Neo4j Browser (optional)

---

## 🚀 After Schema Creation

Once the schema is created, we'll proceed to:

1. **Implement KGRetrievalAgent** class
   - File: `src/agents/kg_retrieval.py`
   - Methods: query_similar_incidents, find_causal_paths, etc.

2. **Create sample data** for testing
   - Populate with sample incidents
   - Test queries

3. **Test the agent** with real log parser output
   - Integration test
   - Validate results

---

## 🐛 Troubleshooting

### Issue: "Authentication failed"
```bash
# Check Neo4j status
sudo systemctl status neo4j  # For system install
docker ps | grep neo4j       # For Docker

# Reset password (if needed)
# For system install:
sudo neo4j-admin set-initial-password new_password

# For Docker:
docker exec -it neo4j-container neo4j-admin set-initial-password new_password
```

### Issue: "Connection refused"
```bash
# Check if Neo4j is running
sudo systemctl start neo4j  # For system install
docker start neo4j-rca      # For Docker

# Check ports
sudo netstat -tulpn | grep 7687
```

### Issue: "Database not found"
- Default database is "neo4j"
- No need to create it manually
- It's created automatically on first connection

---

## 📊 Progress

```
✅ Neo4j installed
⏳ Connection verified
⏳ Schema created
⏳ KGRetrievalAgent implemented
⏳ Tests passing
```

---

**Next**: Update passwords and run the connection test!

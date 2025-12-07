# Quick Fix: Agent Initialization Issue ✅

**Issue**: `TypeError: got multiple values for keyword argument 'name'`

**Cause**: Agents have hardcoded default names and models in their `__init__` methods, but test script was passing them again.

---

## Fixed Agents

### **1. KGRetrievalAgent**
**Before** (❌ Error):
```python
kg_agent = KGRetrievalAgent(
    name="kg_retrieval",  # ❌ Conflicts with hardcoded name
    model="qwen2:7b",
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="1997Amaterasu"
)
```

**After** (✅ Fixed):
```python
kg_agent = KGRetrievalAgent(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="1997Amaterasu"
)
```

### **2. RCA Reasoners**
**Before** (❌ Error):
```python
log_reasoner = LogFocusedReasoner(
    name="log_focused",  # ❌ Conflicts
    model="mistral:7b"   # ❌ Conflicts
)
```

**After** (✅ Fixed):
```python
log_reasoner = LogFocusedReasoner()  # Uses defaults
kg_reasoner = KGFocusedReasoner()    # Uses defaults
hybrid_reasoner = HybridReasoner()   # Uses defaults
```

### **3. Judge Agent**
**Before** (❌ Error):
```python
judge = JudgeAgent(
    name="judge",      # ❌ Conflicts
    model="qwen2:7b"   # ❌ Conflicts
)
```

**After** (✅ Fixed):
```python
judge = JudgeAgent()  # Uses defaults
```

---

## Default Values

### **LogFocusedReasoner**:
- Name: `"LogFocusedReasoner"`
- Model: `"mistral:7b"`
- Reasoning Type: `"log_focused"`

### **KGFocusedReasoner**:
- Name: `"KGFocusedReasoner"`
- Model: `"llama2:7b"`
- Reasoning Type: `"kg_focused"`

### **HybridReasoner**:
- Name: `"HybridReasoner"`
- Model: `"qwen2:7b"`
- Reasoning Type: `"hybrid"`

### **JudgeAgent**:
- Name: `"JudgeAgent"`
- Model: `"qwen2:7b"`

---

## Test Script Updated

**File**: `tests/test_hdfs_real_data.py`

**Changes**:
1. ✅ Removed `name` and `model` from reasoner initialization
2. ✅ Fixed KG agent parameters
3. ✅ Simplified judge initialization

**Status**: Ready to run! 🚀

---

### **4. Debate Coordinator**
**Before** (❌ Error):
```python
coordinator = DebateCoordinator(
    reasoners={  # ❌ Wrong parameter!
        "log_focused": log_reasoner,
        "kg_focused": kg_reasoner,
        "hybrid": hybrid_reasoner
    },
    judge=judge
)
```

**After** (✅ Fixed):
```python
coordinator = DebateCoordinator(
    log_reasoner=log_reasoner,      # ✅ Individual parameters
    kg_reasoner=kg_reasoner,        # ✅ Individual parameters
    hybrid_reasoner=hybrid_reasoner, # ✅ Individual parameters
    judge=judge,
    max_rounds=3,
    convergence_threshold=5.0
)
```

---

## Run the Test

```bash
python tests/test_hdfs_real_data.py 1
```

**Expected**: Test should now run without initialization errors!

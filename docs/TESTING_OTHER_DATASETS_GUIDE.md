# Testing on Different Datasets - Complete Guide 🚀

**Date**: December 7, 2025  
**Current Status**: HDFS testing complete ✅  
**Next**: Test Hadoop and Spark datasets

---

## 📋 Quick Overview

### **What We've Done**
- ✅ HDFS: 3 scenarios tested (91.7/100 average)

### **What's Next**
- 🔄 Hadoop: Test multiple scenarios
- 🔄 Spark: Test multiple scenarios
- 📊 Compare results across datasets
- 🎯 Measure accuracy against ground truth

---

## 🗂️ Available Datasets

### **1. HDFS (Hadoop Distributed File System)** ✅ **COMPLETE**

**Location**: `loghub/HDFS/`

**Files**:
- `HDFS_2k.log_structured.csv` (415 KB)
- `HDFS_2k.log_templates.csv`

**Characteristics**:
- 2000 log entries total
- Block-level traces
- Anomaly labels available
- Disk, hardware, replication failures

**Status**: ✅ **Tested** (3 scenarios, 91.7/100 average)

---

### **2. Hadoop** 🔄 **NEXT TO TEST**

**Location**: `loghub/Hadoop/`

**Files**:
- `Hadoop_2k.log_structured.csv` (1.1 MB)
- `Hadoop_2k.log_templates.csv`
- `abnormal_label.txt` ← **Ground truth available!**

**Characteristics**:
- 2000 log entries
- Application-level logs
- **Labeled abnormal/normal jobs**
- Known failure types:
  - Machine down
  - Network issue
  - Disk full
  - Software bug

**Why Important**:
- ✅ Has ground truth labels
- ✅ Known failure categories
- ✅ Can measure accuracy
- ✅ Different from HDFS (application vs block level)

**Expected Scenarios**: 5-10 (depending on log distribution)

---

### **3. Spark** 🔄 **NEXT TO TEST**

**Location**: `loghub/Spark/`

**Files**:
- `Spark_2k.log_structured.csv` (1.4 MB)
- `Spark_2k.log_templates.csv`

**Characteristics**:
- 2000 log entries
- 32 machine cluster
- Performance and resource issues
- Executor failures, task retries

**Why Important**:
- ✅ Different system (Spark vs Hadoop/HDFS)
- ✅ Performance-focused failures
- ✅ Resource allocation issues
- ✅ Validates generalization

**Expected Scenarios**: 5-10

---

## 🚀 How to Test Different Datasets

### **Option 1: Create New Test Scripts** (Recommended)

Each dataset gets its own test script for clarity and customization.

#### **Step 1: Create Hadoop Test Script**

```bash
# Copy HDFS test as template
cp tests/test_hdfs_real_data.py tests/test_hadoop_real_data.py
```

#### **Step 2: Modify for Hadoop**

Edit `tests/test_hadoop_real_data.py`:

```python
# Change dataset name
def test_hadoop_scenario(scenario_id):
    """Test single Hadoop scenario."""
    
    print("="*70)
    print("HADOOP REAL DATA TEST")  # ← Changed
    print("="*70)
    print(f"Testing Scenario {scenario_id}\n")
    
    # Step 1: Load Hadoop data
    print_section("STEP 1: LOADING HADOOP DATA")  # ← Changed
    
    loader = LoghubLoader(root="loghub")
    scenarios = loader.load_dataset("Hadoop")  # ← Changed
    
    # ... rest is the same ...
    
    # Save results
    output_file = f"hadoop_scenario_{scenario_id}_results.json"  # ← Changed
```

#### **Step 3: Run Hadoop Tests**

```bash
# Test single scenario
python tests/test_hadoop_real_data.py 1

# Test all scenarios
python tests/test_hadoop_real_data.py
```

#### **Step 4: Repeat for Spark**

```bash
# Create Spark test
cp tests/test_hdfs_real_data.py tests/test_spark_real_data.py

# Modify for Spark (same changes as Hadoop)
# Run tests
python tests/test_spark_real_data.py
```

---

### **Option 2: Unified Test Script** (Alternative)

Create a single script that tests all datasets.

#### **Create `tests/test_all_datasets.py`**

```python
#!/usr/bin/env python3
"""
Test RCA system on all available datasets.
"""

import sys
from src.utils.loghub_loader import LoghubLoader
from src.agents.kg_retrieval import KGRetrievalAgent
from src.agents.rca_log_reasoner import LogFocusedReasoner
from src.agents.rca_kg_reasoner import KGFocusedReasoner
from src.agents.rca_hybrid_reasoner import HybridReasoner
from src.agents.judge_agent import JudgeAgent
from src.debate.debate_coordinator import DebateCoordinator
import json


def test_dataset(dataset_name, num_scenarios=3):
    """Test a dataset with multiple scenarios."""
    
    print("\n" + "="*70)
    print(f"{dataset_name.upper()} DATASET TEST")
    print("="*70)
    
    # Load dataset
    loader = LoghubLoader(root="loghub")
    scenarios = loader.load_dataset(dataset_name)
    
    print(f"✓ Loaded {len(scenarios)} scenarios from {dataset_name}")
    
    # Test scenarios
    results = []
    for i in range(min(num_scenarios, len(scenarios))):
        scenario_id = i + 1
        print(f"\n--- Testing Scenario {scenario_id} ---")
        
        scenario = scenarios[i]
        
        # Run RCA pipeline (same as before)
        # ... (copy from test_hdfs_real_data.py)
        
        results.append({
            "scenario_id": scenario_id,
            "final_score": final_score,
            "category": category,
            # ... other metrics
        })
    
    # Summary
    avg_score = sum(r["final_score"] for r in results) / len(results)
    print(f"\n{dataset_name} Average Score: {avg_score:.1f}/100")
    
    return results


def main():
    """Test all datasets."""
    
    datasets = ["HDFS", "Hadoop", "Spark"]
    all_results = {}
    
    for dataset in datasets:
        try:
            results = test_dataset(dataset, num_scenarios=3)
            all_results[dataset] = results
        except Exception as e:
            print(f"Error testing {dataset}: {e}")
    
    # Save combined results
    with open("all_datasets_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print("\n" + "="*70)
    print("ALL DATASETS TESTED")
    print("="*70)
    
    # Print summary
    for dataset, results in all_results.items():
        avg = sum(r["final_score"] for r in results) / len(results)
        print(f"{dataset}: {avg:.1f}/100 ({len(results)} scenarios)")


if __name__ == "__main__":
    main()
```

#### **Run All Datasets**

```bash
python tests/test_all_datasets.py
```

---

## 📊 Recommended Testing Approach

### **Phase 1: Individual Dataset Testing** (Days 3-4)

**Day 3 Morning: Hadoop**
```bash
# Create Hadoop test script
cp tests/test_hdfs_real_data.py tests/test_hadoop_real_data.py

# Modify for Hadoop
vim tests/test_hadoop_real_data.py

# Test 3 scenarios
python tests/test_hadoop_real_data.py

# Expected time: ~15-20 minutes
```

**Day 3 Afternoon: Spark**
```bash
# Create Spark test script
cp tests/test_hdfs_real_data.py tests/test_spark_real_data.py

# Modify for Spark
vim tests/test_spark_real_data.py

# Test 3 scenarios
python tests/test_spark_real_data.py

# Expected time: ~15-20 minutes
```

### **Phase 2: Analysis and Comparison** (Day 4)

**Compare Results**:
```bash
# View all results
ls *_results.json

# Compare averages
python -c "
import json
import glob

for file in glob.glob('*_scenario_*_results.json'):
    with open(file) as f:
        data = json.load(f)
        print(f'{file}: {data[\"final_score\"]}/100')
"
```

### **Phase 3: Ground Truth Validation** (Day 5)

**For Hadoop** (has labels):
```bash
# Check abnormal_label.txt
cat loghub/Hadoop/abnormal_label.txt

# Compare with our predictions
python scripts/validate_accuracy.py
```

---

## 🎯 What to Look For

### **1. Consistency Across Datasets**

**Questions**:
- Do scores remain high (>85/100)?
- Is convergence consistent?
- Does hybrid reasoner still win?

**Expected**:
- ✅ Scores: 85-95/100 range
- ✅ Convergence: 2-3 rounds
- ✅ Winner: Hybrid reasoner

### **2. Category Distribution**

**Questions**:
- What categories appear in each dataset?
- Are they appropriate for the system?

**Expected**:
- HDFS: Network, config, disk
- Hadoop: Machine, network, disk, software
- Spark: Resource, performance, executor

### **3. Dataset-Specific Patterns**

**Questions**:
- Does system adapt to different log formats?
- Are hypotheses appropriate for each system?

**Expected**:
- ✅ HDFS: Block-level issues
- ✅ Hadoop: Job-level issues
- ✅ Spark: Executor/task issues

### **4. Ground Truth Accuracy** (Hadoop)

**Questions**:
- Do our predictions match labels?
- What's the accuracy rate?

**Expected**:
- ✅ Accuracy: >70% (good)
- ✅ Accuracy: >80% (excellent)

---

## 📈 Expected Results

### **Hadoop Dataset**

**Predictions**:
- Average score: 88-92/100
- Categories: Machine, network, disk, software
- Convergence: 2-3 rounds
- Winner: Hybrid reasoner

**Challenges**:
- Application-level logs (different from HDFS)
- More diverse failure types
- May have more complex patterns

### **Spark Dataset**

**Predictions**:
- Average score: 85-90/100
- Categories: Resource, performance, executor
- Convergence: 2-3 rounds
- Winner: Hybrid reasoner

**Challenges**:
- Performance issues (not just failures)
- Resource allocation complexity
- Task retry patterns

---

## 🔧 Troubleshooting

### **Issue 1: Dataset Not Loading**

**Error**: `FileNotFoundError: loghub/Hadoop/...`

**Solution**:
```bash
# Check if dataset exists
ls -la loghub/Hadoop/

# If missing, download from loghub
# Or check dataset name spelling
```

### **Issue 2: Different CSV Format**

**Error**: `KeyError: 'Content'` or similar

**Solution**:
```python
# Check CSV columns
import pandas as pd
df = pd.read_csv("loghub/Hadoop/Hadoop_2k.log_structured.csv")
print(df.columns)

# Adjust LoghubLoader if needed
```

### **Issue 3: Too Many/Few Scenarios**

**Error**: Not enough scenarios created

**Solution**:
```python
# Adjust chunk size in LoghubLoader
# Or test with available scenarios
python tests/test_hadoop_real_data.py 1 2  # Test specific scenarios
```

---

## 📊 Results Comparison Template

### **Create Comparison Script**

```python
#!/usr/bin/env python3
"""Compare results across datasets."""

import json
import glob
from collections import defaultdict

def compare_datasets():
    """Compare all dataset results."""
    
    datasets = defaultdict(list)
    
    # Load all results
    for file in glob.glob("*_scenario_*_results.json"):
        with open(file) as f:
            data = json.load(f)
            dataset = data["dataset"]
            datasets[dataset].append(data)
    
    # Print comparison
    print("\n" + "="*70)
    print("DATASET COMPARISON")
    print("="*70)
    
    for dataset, results in datasets.items():
        scores = [r["final_score"] for r in results]
        rounds = [r["total_rounds"] for r in results]
        
        print(f"\n{dataset}:")
        print(f"  Scenarios: {len(results)}")
        print(f"  Average Score: {sum(scores)/len(scores):.1f}/100")
        print(f"  Score Range: {min(scores)}-{max(scores)}")
        print(f"  Average Rounds: {sum(rounds)/len(rounds):.1f}")
        print(f"  Convergence Rate: {sum(r['convergence'] for r in results)/len(results)*100:.0f}%")
    
    # Overall summary
    all_scores = [r["final_score"] for results in datasets.values() for r in results]
    print(f"\n{'='*70}")
    print(f"OVERALL:")
    print(f"  Total Scenarios: {len(all_scores)}")
    print(f"  Overall Average: {sum(all_scores)/len(all_scores):.1f}/100")
    print(f"  Overall Range: {min(all_scores)}-{max(all_scores)}")

if __name__ == "__main__":
    compare_datasets()
```

**Run**:
```bash
python scripts/compare_datasets.py
```

---

## 🎯 Success Criteria

### **Per Dataset**

- ✅ Average score: >85/100
- ✅ Convergence rate: >80%
- ✅ No crashes or errors
- ✅ Reasonable categories

### **Cross-Dataset**

- ✅ Consistent performance (±10 points)
- ✅ Same winner (Hybrid)
- ✅ Similar convergence patterns
- ✅ Appropriate category diversity

### **Ground Truth** (Hadoop)

- ✅ Accuracy: >70%
- ✅ Category match: >60%
- ✅ No systematic errors

---

## 📝 Documentation Template

### **After Each Dataset**

Create `docs/[DATASET]_TESTING_RESULTS.md`:

```markdown
# [Dataset] Testing Results

## Summary
- Scenarios tested: X
- Average score: XX/100
- Convergence rate: XX%

## Detailed Results
[Scenario-by-scenario breakdown]

## Key Findings
[Insights and observations]

## Comparison with HDFS
[Similarities and differences]
```

---

## 🚀 Quick Start Commands

### **Test Hadoop** (Recommended Next)

```bash
# 1. Create test script
cp tests/test_hdfs_real_data.py tests/test_hadoop_real_data.py

# 2. Edit dataset name (3 places)
sed -i 's/HDFS/Hadoop/g' tests/test_hadoop_real_data.py
sed -i 's/hdfs/hadoop/g' tests/test_hadoop_real_data.py

# 3. Run tests
python tests/test_hadoop_real_data.py

# Expected output: 3 scenarios, ~15-20 minutes
```

### **Test Spark**

```bash
# 1. Create test script
cp tests/test_hdfs_real_data.py tests/test_spark_real_data.py

# 2. Edit dataset name
sed -i 's/HDFS/Spark/g' tests/test_spark_real_data.py
sed -i 's/hdfs/spark/g' tests/test_spark_real_data.py

# 3. Run tests
python tests/test_spark_real_data.py

# Expected output: 3 scenarios, ~15-20 minutes
```

### **Compare All Results**

```bash
# View all results
ls -lh *_scenario_*_results.json

# Quick comparison
for f in *_scenario_*_results.json; do
    echo "$f: $(jq '.final_score' $f)/100"
done
```

---

## 📅 Recommended Timeline

### **Day 3 (Tomorrow)**

**Morning** (2-3 hours):
- ✅ Create Hadoop test script
- ✅ Run Hadoop tests (3 scenarios)
- ✅ Analyze Hadoop results

**Afternoon** (2-3 hours):
- ✅ Create Spark test script
- ✅ Run Spark tests (3 scenarios)
- ✅ Analyze Spark results

**Evening** (1 hour):
- ✅ Compare all three datasets
- ✅ Document findings
- ✅ Identify patterns

### **Day 4** (Optional Extended Testing)

- Test more scenarios per dataset
- Deep dive into specific failures
- Ground truth validation (Hadoop)

### **Day 5** (Analysis & Documentation)

- Create comprehensive comparison
- Measure accuracy metrics
- Prepare Week 3 summary report

---

## 🎉 Summary

### **How to Test Different Datasets**

**Simple Method**:
1. Copy HDFS test script
2. Change dataset name (3 places)
3. Run tests
4. Compare results

**Time Required**:
- Per dataset: ~15-20 minutes
- Total (Hadoop + Spark): ~30-40 minutes

### **What to Expect**

**Hadoop**:
- Similar performance to HDFS
- Different categories (machine, software)
- Ground truth available for validation

**Spark**:
- Slightly different challenges
- Performance-focused issues
- Resource allocation patterns

### **Success Indicators**

- ✅ Scores: 85-95/100 range
- ✅ Consistent winner: Hybrid
- ✅ Convergence: 2-3 rounds
- ✅ No crashes or errors

---

**Ready to test Hadoop and Spark! Let's go! 🚀**

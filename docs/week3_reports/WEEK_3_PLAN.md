# Week 3: Real Data Testing Plan 🚀

**Start Date**: December 7, 2025  
**End Date**: December 13, 2025  
**Status**: 🟢 In Progress

---

## 🎯 Objectives

1. **Test system on real loghub datasets** with actual failure scenarios
2. **Measure accuracy** against ground truth labels
3. **Analyze refinement patterns** and multi-agent collaboration
4. **Validate system performance** on production-like data
5. **Document findings** for paper and future optimization

---

## 📊 Selected Datasets

Based on loghub availability and research value, we'll test on:

### **1. HDFS (Hadoop Distributed File System)**
**Location**: `loghub/HDFS/`  
**Files**: 
- `HDFS_2k.log` (288 KB raw logs)
- `HDFS_2k.log_structured.csv` (415 KB structured)
- `HDFS_2k.log_templates.csv` (templates)

**Characteristics**:
- Block-level traces with anomaly labels
- Normal/anomaly classification available
- Well-studied in literature
- Disk, hardware, and replication failures

**Ground Truth**: Available in preprocessed datasets
- `anomaly_label.csv`
- `Event_traces.csv`

**Why Selected**: 
- Matches our sample data (HDFS disk failures)
- Has ground truth labels
- Well-documented failure types
- Good baseline for comparison

---

### **2. Hadoop (MapReduce Framework)**
**Location**: `loghub/Hadoop/`  
**Files**:
- `Hadoop_2k.log` (385 KB raw logs)
- `Hadoop_2k.log_structured.csv` (541 KB structured)
- `Hadoop_2k.log_templates.csv` (templates)

**Characteristics**:
- 46 cores across 5 machines
- WordCount and PageRank applications
- Injected failures with labels

**Failure Types**:
1. **Machine down**: Server shutdown during execution
2. **Network disconnection**: Network failure simulation
3. **Disk full**: Disk space exhaustion

**Ground Truth**: Available in `abnormal_label.txt`

**Why Selected**:
- Multiple failure types (machine, network, disk)
- Labeled normal/abnormal job IDs
- Distributed system failures
- Real application workloads

---

### **3. Spark (Big Data Processing)**
**Location**: `loghub/Spark/`  
**Files**:
- `Spark_2k.log` (196 KB raw logs)
- `Spark_2k.log_structured.csv` (305 KB structured)
- `Spark_2k.log_templates.csv` (templates)

**Characteristics**:
- 32 machines cluster
- Machine-level log aggregation
- Mix of normal and abnormal runs
- Performance and resource issues

**Failure Types**:
- Application failures
- Resource exhaustion
- Performance degradation
- Machine failures

**Ground Truth**: Unlabeled (we'll need to create scenarios)

**Why Selected**:
- Different from HDFS/Hadoop (analytics engine)
- Performance-related failures
- Large-scale cluster
- Tests system on unlabeled data

---

### **4. OpenStack (Cloud Infrastructure)** [Optional]
**Location**: `loghub/OpenStack/`  
**Files**:
- `OpenStack_2k.log` (595 KB raw logs)
- `OpenStack_2k.log_structured.csv` (720 KB structured)

**Characteristics**:
- Cloud infrastructure logs
- Service orchestration failures
- API and component interactions

**Why Selected**:
- Different domain (cloud vs. big data)
- Complex service dependencies
- Tests KG retrieval on service relationships

---

### **5. Zookeeper (Coordination Service)** [Optional]
**Location**: `loghub/Zookeeper/`  
**Files**:
- `Zookeeper_2k.log` (280 KB raw logs)
- `Zookeeper_2k.log_structured.csv` (372 KB structured)

**Characteristics**:
- Distributed coordination service
- Leader election failures
- Network partition issues

**Why Selected**:
- Coordination and consensus failures
- Different failure patterns
- Tests reasoning on distributed protocols

---

## 📋 Week 3 Schedule

### **Day 1 (Dec 7): Dataset Preparation** ✅ In Progress
- [x] Explore available datasets
- [x] Select primary datasets (HDFS, Hadoop, Spark)
- [ ] Load and inspect structured CSV files
- [ ] Understand log formats and templates
- [ ] Document dataset characteristics

### **Day 2 (Dec 8): Ground Truth Creation**
- [ ] Extract HDFS anomaly labels
- [ ] Extract Hadoop failure labels
- [ ] Create incident scenarios for each dataset
- [ ] Define expected root causes
- [ ] Document evaluation criteria

### **Day 3 (Dec 9): Test Infrastructure**
- [ ] Build real data loader
- [ ] Create incident scenario extractor
- [ ] Implement accuracy measurement
- [ ] Build batch testing script
- [ ] Add result collection and reporting

### **Day 4 (Dec 10): Initial Testing**
- [ ] Test on HDFS dataset
- [ ] Collect results and metrics
- [ ] Analyze hypothesis quality
- [ ] Measure accuracy vs. ground truth
- [ ] Document findings

### **Day 5 (Dec 11): Extended Testing**
- [ ] Test on Hadoop dataset
- [ ] Test on Spark dataset
- [ ] Compare results across datasets
- [ ] Analyze refinement patterns
- [ ] Identify common issues

### **Day 6 (Dec 12): Analysis & Optimization**
- [ ] Aggregate all results
- [ ] Calculate performance metrics
- [ ] Identify optimization opportunities
- [ ] Test optimizations if time permits
- [ ] Prepare findings document

### **Day 7 (Dec 13): Documentation & Week 3 Wrap-up**
- [ ] Create comprehensive results report
- [ ] Document accuracy metrics
- [ ] Analyze multi-agent value
- [ ] Identify Week 4 priorities
- [ ] Prepare Week 3 completion document

---

## 🎯 Success Criteria

### **Minimum (Must Achieve)**:
- [ ] Test on at least 2 datasets (HDFS + Hadoop)
- [ ] Measure accuracy on labeled data
- [ ] Document refinement improvements
- [ ] Identify at least 3 optimization opportunities
- [ ] Complete Week 3 report

### **Target (Should Achieve)**:
- [ ] Test on 3 datasets (HDFS + Hadoop + Spark)
- [ ] Achieve >60% accuracy on ground truth
- [ ] Show visible improvement in all cases
- [ ] Analyze cross-dataset patterns
- [ ] Create reusable test framework

### **Stretch (Nice to Have)**:
- [ ] Test on 5 datasets (add OpenStack + Zookeeper)
- [ ] Achieve >70% accuracy
- [ ] Implement and test optimizations
- [ ] Create visualization dashboard
- [ ] Prepare paper-ready figures

---

## 📊 Metrics to Track

### **Accuracy Metrics**:
1. **Hypothesis Accuracy**: % of hypotheses matching ground truth
2. **Top-1 Accuracy**: % of top hypotheses matching ground truth
3. **Top-3 Accuracy**: % where ground truth in top 3
4. **Category Accuracy**: % correct failure category

### **Improvement Metrics**:
1. **Score Improvement**: Average score gain per round
2. **Round-over-Round**: Improvement trajectory
3. **Convergence Rate**: Average rounds to convergence
4. **Quality Improvement**: Evidence and reasoning enhancement

### **Multi-Agent Metrics**:
1. **Reasoner Contribution**: Win rate per reasoner
2. **Cross-Learning**: Hypothesis evolution patterns
3. **Collaboration Value**: Hybrid vs. individual performance
4. **Feedback Utilization**: How feedback changes hypotheses

### **System Performance**:
1. **Runtime**: Time per dataset
2. **LLM Calls**: Number of API calls
3. **Token Usage**: Total tokens consumed
4. **Convergence Efficiency**: Rounds needed

---

## 🔧 Technical Tasks

### **1. Data Loading**
```python
# data/loaders/loghub_loader.py
- Load structured CSV files
- Parse log templates
- Extract incident traces
- Load ground truth labels
```

### **2. Scenario Creation**
```python
# data/scenarios/incident_scenarios.py
- Define incident scenarios
- Map to ground truth
- Create test cases
- Document expected outcomes
```

### **3. Testing Framework**
```python
# tests/test_real_data.py
- Batch testing script
- Accuracy measurement
- Result collection
- Report generation
```

### **4. Evaluation**
```python
# evaluation/metrics.py
- Accuracy calculators
- Improvement trackers
- Statistical analysis
- Visualization tools
```

---

## 📈 Expected Outcomes

### **Quantitative**:
- Accuracy: 60-75% on labeled data
- Improvement: +3-5 points per round
- Convergence: 2-3 rounds average
- Runtime: 3-5 minutes per dataset

### **Qualitative**:
- Hypotheses match failure types
- Evidence aligns with logs
- Resolutions are actionable
- Multi-agent value visible

### **Insights**:
- Which reasoner performs best per failure type
- How refinement improves hypotheses
- Where system struggles
- What optimizations are needed

---

## 🚧 Potential Challenges

### **1. Ground Truth Availability**
**Challenge**: Not all datasets have detailed labels  
**Solution**: 
- Focus on HDFS and Hadoop (labeled)
- Create scenarios for Spark
- Use failure type categories

### **2. Log Format Variability**
**Challenge**: Different log structures across datasets  
**Solution**:
- Use structured CSV files
- Adapt log parser for each format
- Focus on key fields (timestamp, level, message)

### **3. Accuracy Measurement**
**Challenge**: Matching LLM hypotheses to ground truth  
**Solution**:
- Use semantic similarity
- Match failure categories
- Manual review of top hypotheses
- Multiple evaluation criteria

### **4. Runtime Constraints**
**Challenge**: Testing multiple datasets takes time  
**Solution**:
- Start with smaller samples
- Parallel processing where possible
- Focus on quality over quantity
- Use efficient prompts

---

## 🎯 Immediate Next Steps (Today)

### **Step 1: Load HDFS Data** ✅ Next
```bash
# Inspect structured CSV
head -20 loghub/HDFS/HDFS_2k.log_structured.csv

# Check templates
cat loghub/HDFS/HDFS_2k.log_templates.csv

# Look for ground truth files
ls -la loghub/HDFS/
```

### **Step 2: Create Data Loader**
```python
# Create: src/utils/loghub_loader.py
- Load structured CSV
- Parse log events
- Extract incident traces
- Return in system format
```

### **Step 3: Create Test Scenario**
```python
# Create: data/scenarios/hdfs_scenarios.py
- Define 3-5 incident scenarios
- Map to ground truth
- Document expected root causes
```

### **Step 4: Build Test Script**
```python
# Create: tests/test_hdfs_real_data.py
- Load HDFS data
- Run debate protocol
- Measure accuracy
- Generate report
```

---

## 📚 Deliverables

### **Code**:
1. `src/utils/loghub_loader.py` - Data loader
2. `data/scenarios/` - Incident scenarios
3. `tests/test_real_data.py` - Testing framework
4. `evaluation/metrics.py` - Evaluation tools

### **Documentation**:
1. `docs/WEEK_3_RESULTS.md` - Results report
2. `docs/datasets/` - Dataset documentation
3. `docs/evaluation/` - Evaluation methodology

### **Data**:
1. Test results (JSON/CSV)
2. Accuracy metrics
3. Hypothesis examples
4. Failure analysis

---

## 🎉 Success Definition

**Week 3 is successful if**:
1. ✅ Tested on at least 2 real datasets
2. ✅ Measured accuracy with ground truth
3. ✅ Documented refinement improvements
4. ✅ Identified optimization opportunities
5. ✅ Created reusable test framework
6. ✅ Prepared for Week 4 (KG expansion)

---

**Let's build and test on real data! 🚀**

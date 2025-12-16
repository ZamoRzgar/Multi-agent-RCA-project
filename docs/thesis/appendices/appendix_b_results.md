# Appendix B: Full Experimental Results

## B.1 Multi-Agent Pipeline Results (Week 6)

### B.1.1 Strict Evaluation (4-class) - Full Metrics

```json
{
  "strict": {
    "labels": ["normal", "machine_down", "network_disconnection", "disk_full"],
    "accuracy": 0.2182,
    "macro_avg": {
      "precision": 0.4167,
      "recall": 0.3056,
      "f1": 0.2162
    },
    "per_class": {
      "normal": {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "support": 11
      },
      "machine_down": {
        "precision": 0.50,
        "recall": 0.1429,
        "f1": 0.2222,
        "support": 28
      },
      "network_disconnection": {
        "precision": 0.1667,
        "recall": 0.8571,
        "f1": 0.2791,
        "support": 7
      },
      "disk_full": {
        "precision": 1.0,
        "recall": 0.2222,
        "f1": 0.3636,
        "support": 9
      }
    },
    "total": 55,
    "unknown_predictions": 9
  }
}
```

### B.1.2 Coarse Evaluation (3-class) - Full Metrics

```json
{
  "coarse": {
    "labels": ["normal", "connectivity", "disk_full"],
    "accuracy": 0.6182,
    "macro_avg": {
      "precision": 0.5758,
      "recall": 0.3788,
      "f1": 0.3913
    },
    "per_class": {
      "normal": {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "support": 11
      },
      "connectivity": {
        "precision": 0.7273,
        "recall": 0.9143,
        "f1": 0.8101,
        "support": 35
      },
      "disk_full": {
        "precision": 1.0,
        "recall": 0.2222,
        "f1": 0.3636,
        "support": 9
      }
    },
    "total": 55,
    "unknown_predictions": 9
  }
}
```

### B.1.3 Confusion Matrix (Strict)

| Ground Truth \ Predicted | normal | machine_down | network_disc | disk_full | unknown |
|--------------------------|--------|--------------|--------------|-----------|---------|
| normal (n=11) | 0 | 2 | 6 | 0 | 3 |
| machine_down (n=28) | 0 | 4 | 21 | 0 | 3 |
| network_disconnection (n=7) | 0 | 1 | 6 | 0 | 0 |
| disk_full (n=9) | 0 | 1 | 3 | 2 | 3 |

### B.1.4 Confusion Matrix (Coarse)

| Ground Truth \ Predicted | normal | connectivity | disk_full | unknown |
|--------------------------|--------|--------------|-----------|---------|
| normal (n=11) | 0 | 8 | 0 | 3 |
| connectivity (n=35) | 0 | 32 | 0 | 3 |
| disk_full (n=9) | 0 | 4 | 2 | 3 |

## B.2 Single-Agent Baseline Results (Week 8)

### B.2.1 Strict Evaluation (4-class) - Full Metrics

```json
{
  "strict": {
    "labels": ["normal", "machine_down", "network_disconnection", "disk_full"],
    "accuracy": 0.5091,
    "macro_avg": {
      "precision": 0.1321,
      "recall": 0.25,
      "f1": 0.1728
    },
    "per_class": {
      "normal": {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "support": 11
      },
      "machine_down": {
        "precision": 0.5283,
        "recall": 1.0,
        "f1": 0.6914,
        "support": 28
      },
      "network_disconnection": {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "support": 7
      },
      "disk_full": {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "support": 9
      }
    },
    "total": 55,
    "unknown_predictions": 0
  }
}
```

### B.2.2 Coarse Evaluation (3-class) - Full Metrics

```json
{
  "coarse": {
    "labels": ["normal", "connectivity", "disk_full"],
    "accuracy": 0.6182,
    "macro_avg": {
      "precision": 0.2138,
      "recall": 0.3238,
      "f1": 0.2576
    },
    "per_class": {
      "normal": {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "support": 11
      },
      "connectivity": {
        "precision": 0.6415,
        "recall": 0.9714,
        "f1": 0.7727,
        "support": 35
      },
      "disk_full": {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "support": 9
      }
    },
    "total": 55,
    "unknown_predictions": 0
  }
}
```

### B.2.3 Confusion Matrix (Strict)

| Ground Truth \ Predicted | normal | machine_down | network_disc | disk_full |
|--------------------------|--------|--------------|--------------|-----------|
| normal (n=11) | 0 | 10 | 0 | 1 |
| machine_down (n=28) | 0 | 28 | 0 | 0 |
| network_disconnection (n=7) | 0 | 6 | 0 | 1 |
| disk_full (n=9) | 0 | 9 | 0 | 0 |

### B.2.4 Confusion Matrix (Coarse)

| Ground Truth \ Predicted | normal | connectivity | disk_full |
|--------------------------|--------|--------------|-----------|
| normal (n=11) | 0 | 10 | 1 |
| connectivity (n=35) | 0 | 34 | 1 |
| disk_full (n=9) | 0 | 9 | 0 |

## B.3 Comparative Summary Table

| Metric | Multi-Agent | Single-Agent | Δ (Multi - Single) |
|--------|-------------|--------------|-------------------|
| **Strict Evaluation** |
| Accuracy | 21.8% | 50.9% | -29.1 pp |
| Macro Precision | 41.7% | 13.2% | +28.5 pp |
| Macro Recall | 30.6% | 25.0% | +5.6 pp |
| Macro F1 | 21.6% | 17.3% | +4.3 pp |
| Normal F1 | 0.0% | 0.0% | 0 pp |
| Machine Down F1 | 22.2% | 69.1% | -46.9 pp |
| Network Disc F1 | 27.9% | 0.0% | +27.9 pp |
| Disk Full F1 | 36.4% | 0.0% | +36.4 pp |
| Unknown Predictions | 9 | 0 | +9 |
| **Coarse Evaluation** |
| Accuracy | 61.8% | 61.8% | 0 pp |
| Macro Precision | 57.6% | 21.4% | +36.2 pp |
| Macro Recall | 37.9% | 32.4% | +5.5 pp |
| Macro F1 | 39.1% | 25.8% | +13.3 pp |
| Normal F1 | 0.0% | 0.0% | 0 pp |
| Connectivity F1 | 81.0% | 77.3% | +3.7 pp |
| Disk Full F1 | 36.4% | 0.0% | +36.4 pp |

## B.4 Cross-Dataset Testing Results (Week 3)

### B.4.1 HDFS Dataset

| Scenario | Final Score | Winner | Root Cause Category | Rounds |
|----------|-------------|--------|---------------------|--------|
| 1 | 92/100 | Hybrid | Configuration | 3 |
| 2 | 90/100 | Hybrid | Network | 3 |
| 3 | 93/100 | Hybrid | Configuration | 3 |
| **Average** | **91.7/100** | - | - | **3.0** |

### B.4.2 Hadoop Dataset

| Scenario | Final Score | Winner | Root Cause Category | Rounds |
|----------|-------------|--------|---------------------|--------|
| 1 | 93/100 | Hybrid | Configuration | 2 |
| 2 | 90/100 | Hybrid | Resource | 2 |
| 3 | 90/100 | KG-focused | Network | 2 |
| **Average** | **91.0/100** | - | - | **2.0** |

### B.4.3 Spark Dataset

| Scenario | Final Score | Winner | Root Cause Category | Rounds |
|----------|-------------|--------|---------------------|--------|
| 1 | 90/100 | Hybrid | Configuration | 3 |
| 2 | 92/100 | Hybrid | Memory | 3 |
| 3 | 90/100 | Hybrid | Resource | 3 |
| **Average** | **90.7/100** | - | - | **3.0** |

### B.4.4 Overall Cross-Dataset Summary

| Metric | Value |
|--------|-------|
| Total Scenarios | 9 |
| Average Score | 91.1/100 |
| Convergence Rate | 100% (9/9) |
| Hybrid Win Rate | 89% (8/9) |
| KG-focused Win Rate | 11% (1/9) |
| Average Rounds | 2.7 |

## B.5 Knowledge Graph Statistics

### B.5.1 Node Counts

| Node Type | Count |
|-----------|-------|
| Incident | 14 |
| Entity | 12 |
| RootCause | 12 |
| **Total** | **38** |

### B.5.2 Relationship Counts

| Relationship Type | Count |
|-------------------|-------|
| INVOLVES | ~28 |
| HAS_ROOT_CAUSE | ~14 |
| SIMILAR_TO | ~28 |
| **Total** | **~70** |

### B.5.3 Entity Distribution

| Entity | Type | Incident Count |
|--------|------|----------------|
| Issue | issue | 8 |
| Network | resource | 5 |
| Configuration | config | 4 |
| Failure | issue | 3 |
| Memory | resource | 1 |
| Spark | component | 1 |

### B.5.4 Incidents by Dataset

| Dataset | Incident Count |
|---------|----------------|
| HDFS | 3 |
| Hadoop | 3 |
| Spark | 8 |
| **Total** | **14** |

# Week 6 Final Complete Report — Hadoop1 Ground Truth Validation

**Week**: Week 6 (Dec 13–19, 2025)

## 1) Executive Summary

This week’s objective was to validate the end-to-end **multi-agent RCA pipeline** against the **Hadoop1 labeled dataset** (`loghub/Hadoop1/abnormal_label.txt`). We executed a full run across **all 55 labeled applications**, produced per-application audit artifacts, computed aggregate metrics (accuracy, precision/recall/F1, confusion matrices), and completed a targeted misclassification audit.

**Key result**: Strict injected-failure classification is low due to label/evidence ambiguity (especially `machine_down` vs `network_disconnection`) and because many `normal` labeled apps contain strong error signatures. The system performs substantially better when evaluated as a **coarse operational diagnosis**.

**Headline metric decision (for reporting)**:

- **Primary headline**: **Coarse (3-class) operational diagnosis** (`normal`, `connectivity`, `disk_full`)
- **Secondary metric**: **Strict (4-class) injected-failure match** (`normal`, `machine_down`, `network_disconnection`, `disk_full`)

## 2) Week 6 Goals (What we set out to do)

- Validate Hadoop1 ground-truth labels using the **full RCA pipeline** (not a simplified baseline).
- Produce reproducible evaluation artifacts:
  - Per-app predictions + evidence snippets.
  - Aggregate metrics: accuracy + macro/per-class P/R/F1 + confusion matrices.
- Audit major misclassification patterns and determine the correct reporting stance.

## 3) Deliverables Produced

- **Validation runner**:
  - `scripts/validate_ground_truth.py`

- **Primary outputs (authoritative results)**:
  - `docs/HADOOP1_GROUND_TRUTH_RESULTS.json`
  - `docs/HADOOP1_GROUND_TRUTH_METRICS.json`

- **Week 6 report(s)**:
  - `docs/week6_validation_results/WEEK_6_GROUND_TRUTH_VALIDATION_REPORT.md` (detailed experimental results)
  - `docs/week6_validation_results/WEEK_6_FINAL_COMPLETE_REPORT.md` (this document)

- **Ground truth labels**:
  - `loghub/Hadoop1/abnormal_label.txt`

## 4) System Under Test

### 4.1 Pipeline (high-level)

For each Hadoop1 application ID:

1. Load raw container logs from `loghub/Hadoop1/<application_id>/*.log`.
2. Build minimal `parsed_data` from raw text (events, error messages, entities).
3. Run KG retrieval (best-effort; failures fall back to empty KG context).
4. Run debate protocol (3 reasoners + judge):
   - `LogFocusedReasoner`
   - `KGFocusedReasoner`
   - `HybridReasoner`
   - `JudgeAgent`
   - `DebateCoordinator`
5. Extract judge-selected final hypothesis.
6. Map hypothesis (and/or indicators) to a predicted failure type.

### 4.2 Configuration

- Config file: `config/config.yaml`
- Local LLMs via Ollama (as configured per agent):
  - `qwen2:7b`
  - `mistral:7b`
  - `llama2:7b`
- Neo4j settings are also in `config/config.yaml` (KG is best-effort; evaluation still runs if KG is unavailable).

## 5) Evaluation Protocol

### 5.1 Prediction mapping

The validator records:

- `predicted_failure_type_from_hypothesis`: heuristic mapping from final hypothesis text/category.
- `predicted_failure_type_from_indicators`: regex indicator scoring over sampled raw log text.
- `predicted_failure_type`: the final label used for metrics (hypothesis mapping first; indicator fallback only when hypothesis mapping is `unknown`).

### 5.2 Strict vs coarse evaluation

- **Strict labels (4-class)**:
  - `normal`, `machine_down`, `network_disconnection`, `disk_full`

- **Coarse labels (3-class)**:
  - `connectivity` = (`machine_down` OR `network_disconnection`)
  - `disk_full`
  - `normal`

### 5.3 Evidence and auditability

Each per-application row includes an `evidence_snippet` (up to 25 lines) to support manual audit of why the system predicted a category.

## 6) How to Reproduce

### 6.1 Full run (all labeled Hadoop1 apps)

```bash
python scripts/validate_ground_truth.py --mode hadoop1 --all --max-lines 2500 --max-files 6
```

### 6.2 Output locations

- Results: `docs/HADOOP1_GROUND_TRUTH_RESULTS.json`
- Metrics: `docs/HADOOP1_GROUND_TRUTH_METRICS.json`

## 7) Final Metrics (All 55 Applications)

Source: `docs/HADOOP1_GROUND_TRUTH_METRICS.json`

### 7.1 Strict evaluation (4-class)

- **Accuracy**: **21.8%** (0.2182)
- **Macro avg**:
  - Precision: **41.7%**
  - Recall: **30.6%**
  - F1: **21.6%**
- **Per-class**:
  - `normal`: P=0.0%, R=0.0%, F1=0.0% (n=11)
  - `machine_down`: P=50.0%, R=14.3%, F1=22.2% (n=28)
  - `network_disconnection`: P=16.7%, R=85.7%, F1=27.9% (n=7)
  - `disk_full`: P=100.0%, R=22.2%, F1=36.4% (n=9)
- **Unknown predictions**: 9

### 7.2 Coarse evaluation (3-class)

- **Accuracy**: **61.8%** (0.6182)
- **Macro avg**:
  - Precision: **57.6%**
  - Recall: **37.9%**
  - F1: **39.1%**
- **Per-class**:
  - `normal`: P=0.0%, R=0.0%, F1=0.0% (n=11)
  - `connectivity`: P=72.7%, R=91.4%, F1=81.0% (n=35)
  - `disk_full`: P=100.0%, R=22.2%, F1=36.4% (n=9)
- **Unknown predictions**: 9

## 8) Misclassification Audit (Summary)

This section summarizes the dominant confusion patterns and why they occur, based on `evidence_snippet` saved in `docs/HADOOP1_GROUND_TRUTH_RESULTS.json`.

### 8.1 `normal` labeled apps predicted as connectivity

Representative examples (ground truth `normal`, predicted connectivity):

- `application_1445062781478_0011`
  - Evidence highlights: `Bad response ERROR`, `forcibly closed by the remote host`, `Bad connect ack`.
- `application_1445144423722_0021`
  - Evidence highlights: slow HDFS read processor timings + `Bad response ERROR`.
- `application_1445087491445_0005`
  - Evidence highlights: repeated `forcibly closed by the remote host`.

Interpretation:

- These “normal” runs contain strong operational error signatures; therefore strict `normal` recall is 0.
- In this dataset, `normal` is more consistent with “no injected fault label” than “no error-like events”.

### 8.2 `machine_down` predicted as `network_disconnection`

Representative examples:

- `application_1445062781478_0012`
- `application_1445076437777_0003`
- `application_1445094324383_0005`

Evidence commonly includes connection failure patterns such as `Bad connect ack` and `forcibly closed by the remote host`.

Interpretation:

- A machine going down is observed as connectivity failures at the application/log level.
- Therefore strict discrimination between `machine_down` and `network_disconnection` is frequently not identifiable from the log evidence alone.

### 8.3 `disk_full` predicted as connectivity or unknown

Representative examples:

- `application_1445182159119_0002`
  - Evidence highlights: `DiskChecker$DiskErrorException: Could not find any valid local directory ...`.
- `application_1445182159119_0004`
  - Evidence highlights: `There is not enough space on the disk`.
- `application_1445182159119_0001`
  - Evidence highlights: empty evidence snippet (`[]`), implying missed indicators due to sampling.

Interpretation:

- Disk-full can be mixed with connectivity-like symptoms.
- Disk-full recall is sensitive to evidence capture and whether the final hypothesis text contains disk-related keywords.

## 9) Reporting Stance (What we will claim in Week 6)

### 9.1 Primary headline metric

**Coarse (3-class) operational diagnosis** is the headline because:

- It matches what the system can reliably infer from observable evidence.
- It avoids penalizing symptom-level predictions when strict injected-fault labels are ambiguous.

Headline values:

- Coarse accuracy: **61.8%**
- `connectivity` F1: **81.0%**

### 9.2 Secondary metric (reported transparently)

**Strict (4-class) injected-failure match** is reported as a secondary metric:

- Strict accuracy: **21.8%**

## 10) Limitations / Threats to Validity

- **Label semantics**: `normal` runs often contain error-like events, which conflicts with strict “healthy vs unhealthy” interpretation.
- **Symptom vs injected-fault ambiguity**: `machine_down` vs `network_disconnection` is often indistinguishable in logs.
- **Heuristic mapping**: predicted labels are derived from hypothesis/keywords rather than a supervised classifier.
- **Evidence sampling bias**: error-focused sampling can overweight connectivity indicators.

## 11) Next Steps

- Optional hardening:
  - Fix `JudgeAgent._format_hypotheses` to avoid slicing errors when `suggested_resolution` is not a string.
- Improve disk-full recall:
  - Strengthen disk-full keyword mapping and ensure evidence sampling includes disk-related lines more reliably.
- Define a separate evaluation for “normal detection”:
  - If needed, introduce a dedicated normal/healthy classifier or explicit job-success signals.

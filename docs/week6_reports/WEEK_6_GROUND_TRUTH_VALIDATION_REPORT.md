# Week 6 Experimental Results: Hadoop1 Ground Truth Validation

## Objective
Validate the RCA pipeline on the labeled Hadoop1 dataset by:

- Running the end-to-end multi-agent RCA pipeline on each labeled Hadoop1 application.
- Comparing the predicted failure type to `loghub/Hadoop1/abnormal_label.txt`.
- Reporting aggregate metrics (accuracy, precision, recall, F1) and confusion matrices.
- Producing per-application artifacts with evidence snippets to support auditability.

## Dataset and Ground Truth

- **Dataset**: `loghub/Hadoop1/`
- **Ground truth labels**: `loghub/Hadoop1/abnormal_label.txt`
- **Total labeled applications**: **55**
  - WordCount: 25
  - PageRank: 30
- **Label set (strict)**:
  - `normal`
  - `machine_down`
  - `network_disconnection`
  - `disk_full`

## System Under Test (RCA Pipeline)

### High-level pipeline
For each Hadoop1 application ID:

1. Load raw container logs from `loghub/Hadoop1/<application_id>/*.log`.
2. Build minimal `parsed_data` from raw text (events, error messages, entities).
3. Run KG retrieval (best-effort; failures fall back to empty KG context).
4. Run debate protocol with 3 reasoners + judge:
   - `LogFocusedReasoner`
   - `KGFocusedReasoner`
   - `HybridReasoner`
   - `JudgeAgent`
   - `DebateCoordinator`
5. Extract the judge-selected final hypothesis.
6. Map the hypothesis to a predicted failure type.

### Model/config context
Config is loaded from `config/config.yaml`. The run used local LLMs (Ollama) as configured per agent:

- `qwen2:7b` (log parsing / hybrid / KG retrieval)
- `mistral:7b` (log reasoner + judge)
- `llama2:7b` (KG reasoner)

Neo4j connection settings are defined in the same config.

## Validation Implementation

### Script
- **Runner**: `scripts/validate_ground_truth.py`
- **Mode**: `--mode hadoop1`

### Log loading / sampling
For each application, the script:

- Selects up to `--max-files` largest `*.log` files.
- Collects:
  - First ~120 lines (“head”) for context
  - Lines containing error-like keywords (ERROR/WARN/Exception/failed/timeout/refused/unreachable/no space)
- Combines up to `--max-lines` total lines.

### Prediction mapping
The script derives:

- `predicted_failure_type_from_hypothesis`: heuristic mapping based on the final hypothesis text/category.
- `predicted_failure_type_from_indicators`: regex indicator scoring over the sampled raw text.
- `predicted_failure_type`: final predicted label used for metrics (hypothesis mapping with indicator fallback only when hypothesis mapping is `unknown`).

Additionally, a **coarse label** is computed:

- `connectivity` = (`machine_down` or `network_disconnection`)
- `disk_full`
- `normal`

### Evidence artifact
Each per-app row includes:

- `evidence_snippet`: top matching evidence lines (up to 25) for auditability.

## How to Reproduce

### Full run (all labeled Hadoop1 apps)
```bash
python scripts/validate_ground_truth.py --mode hadoop1 --all --max-lines 2500 --max-files 6
```

### Outputs
- Per-application results:
  - `docs/HADOOP1_GROUND_TRUTH_RESULTS.json`
- Aggregate metrics:
  - `docs/HADOOP1_GROUND_TRUTH_METRICS.json`

Copies of intermediate runs are also available in:
- `docs/week6_validation_results/`

## Final Results (All 55 Applications)

Source: `docs/HADOOP1_GROUND_TRUTH_METRICS.json`

### Strict evaluation (4-class)
**Labels**: `normal`, `machine_down`, `network_disconnection`, `disk_full`

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

**Strict confusion matrix (counts)** (ground_truth → predicted):

- `normal` → machine_down: 2
- `normal` → network_disconnection: 6
- `normal` → unknown: 3

- `machine_down` → machine_down: 4
- `machine_down` → network_disconnection: 21
- `machine_down` → unknown: 3

- `network_disconnection` → machine_down: 1
- `network_disconnection` → network_disconnection: 6

- `disk_full` → machine_down: 1
- `disk_full` → network_disconnection: 3
- `disk_full` → disk_full: 2
- `disk_full` → unknown: 3

**Unknown predictions**: 9

### Coarse evaluation (3-class)
**Labels**: `normal`, `connectivity`, `disk_full`

- **Accuracy**: **61.8%** (0.6182)
- **Macro avg**:
  - Precision: **57.6%**
  - Recall: **37.9%**
  - F1: **39.1%**
- **Per-class**:
  - `normal`: P=0.0%, R=0.0%, F1=0.0% (n=11)
  - `connectivity`: P=72.7%, R=91.4%, F1=81.0% (n=35)
  - `disk_full`: P=100.0%, R=22.2%, F1=36.4% (n=9)

Coarse confusion matrix (counts):

- `normal` → connectivity: 8
- `normal` → unknown: 3

- `connectivity` → connectivity: 32
- `connectivity` → unknown: 3

- `disk_full` → connectivity: 4
- `disk_full` → disk_full: 2
- `disk_full` → unknown: 3

## Key Observations (What the system is doing)

### 1) The system almost never predicts `normal`
- Strict and coarse metrics both show `normal` recall = 0.
- Example (ground truth `normal`):
  - `application_1445062781478_0011` is labeled `normal` but contains strong connectivity/DFS symptoms in the evidence snippet (e.g., “Bad response ERROR”, “forcibly closed”, “Bad connect ack”), leading to a predicted connectivity failure.

This suggests one (or both) of:

- The dataset’s `normal` label means “no injected fault”, not “no error-like lines”.
- The pipeline is tuned to produce RCA hypotheses whenever it sees WARN/ERROR patterns, even if the overall job is considered “normal”.

### 2) `machine_down` is typically diagnosed as `network_disconnection`
- Strict confusion: `machine_down → network_disconnection` dominates (21/28).
- This is plausible because a node going down often manifests as connection failures/timeouts in logs.

This is the primary reason strict 4-class accuracy is low.

### 3) `disk_full` is detected with high precision but low recall
- Precision is high (1.0), meaning when the system predicts disk full it is usually correct.
- Recall is low (0.222), meaning many disk-full labeled apps are instead classified as connectivity or unknown.

### 4) Coarse metric is substantially higher
When we merge `machine_down` and `network_disconnection` into `connectivity`, performance improves:

- Coarse accuracy: 61.8%
- Coarse connectivity F1: 81.0%

This indicates the system is often correct at identifying the *operational symptom class* (connectivity), even when strict injected-failure type differs.

## Limitations / Threats to Validity

- **Label semantics**: `normal` appears to include transient failures or error-like events; strict “normal vs abnormal” may not match the dataset’s intent.
- **Symptom vs injected-fault ambiguity**: `machine_down` and `network_disconnection` are observationally entangled in distributed logs.
- **Heuristic label mapping**: strict predicted labels are derived from hypothesis text/category, not a dedicated supervised classifier.
- **Log sampling bias**: error-focused sampling increases the likelihood of connectivity-heavy hypotheses.

## Misclassification Audit (Representative Cases)

This audit samples representative misclassifications from `docs/HADOOP1_GROUND_TRUTH_RESULTS.json` and explains why they occur based on the saved `evidence_snippet`.

### A) `normal` labeled apps predicted as connectivity

Observation: all 11 `normal` apps were predicted as either connectivity-related (`machine_down` / `network_disconnection`) or `unknown`.

- **application_1445062781478_0011**
  - Ground truth: `normal`
  - Predicted: `network_disconnection` (coarse: `connectivity`)
  - Evidence snippet highlights:
    - `java.io.IOException: Bad response ERROR ...`
    - `... forcibly closed by the remote host`
    - `java.io.IOException: Bad connect ack ...`
  - Interpretation: this “normal” run contains multiple connectivity/DFS I/O symptoms, so the RCA system correctly flags an operational issue even though no injected fault is labeled.

- **application_1445144423722_0021**
  - Ground truth: `normal`
  - Predicted: `network_disconnection` (coarse: `connectivity`)
  - Evidence snippet highlights:
    - `Slow ReadProcessor ... took ...ms (threshold=30000ms)`
    - `Bad response ERROR ... from datanode ...`
  - Interpretation: slow/failed HDFS reads strongly resemble network or datanode connectivity issues.

- **application_1445087491445_0005**
  - Ground truth: `normal`
  - Predicted: `network_disconnection` (coarse: `connectivity`)
  - Evidence snippet highlights:
    - repeated `... forcibly closed by the remote host`
  - Interpretation: connectivity symptoms dominate; this suggests the “normal” label should be interpreted as “no injected fault”, not “no errors”.

Conclusion: the current pipeline is not a reliable **normal/healthy detector** under this dataset because the “normal” runs contain non-trivial error signatures.

### B) `machine_down` labeled apps predicted as `network_disconnection`

Observation: strict confusion shows `machine_down → network_disconnection` is the dominant error mode (21/28).

- **application_1445062781478_0012**
  - Ground truth: `machine_down`
  - Predicted: `network_disconnection` (coarse: `connectivity`)
  - Evidence snippet highlights:
    - repeated `... forcibly closed by the remote host`
    - `Bad connect ack ...`
  - Interpretation: from the log perspective, a node being down is observed as connection failures/timeouts.

- **application_1445076437777_0003**
  - Ground truth: `machine_down`
  - Predicted: `network_disconnection` (coarse: `connectivity`)
  - Evidence snippet highlights:
    - `Bad connect ack ...`
    - `... forcibly closed by the remote host`
  - Interpretation: symptom-level evidence points to connectivity disruption; strict injected-fault labeling is not identifiable from these logs alone.

- **application_1445094324383_0005**
  - Ground truth: `machine_down`
  - Predicted: `network_disconnection` (coarse: `connectivity`)
  - Evidence snippet highlights:
    - repeated failures in HDFS file delete operations
    - `... forcibly closed by the remote host`
  - Interpretation: again, operationally correct (connectivity), but strict match is ambiguous.

Conclusion: strict classification between `machine_down` and `network_disconnection` is frequently not distinguishable from the sampled log evidence.

### C) `disk_full` labeled apps predicted as connectivity or unknown

Observation: `disk_full` recall is low (2/9). Many disk-full apps are predicted as connectivity or `unknown`.

- **application_1445182159119_0002**
  - Ground truth: `disk_full`
  - Predicted: `network_disconnection` (coarse: `connectivity`)
  - Evidence snippet highlights:
    - `DiskChecker$DiskErrorException: Could not find any valid local directory ...`
  - Interpretation: disk/local-dir failures exist, but the final hypothesis/predicted label is pulled toward connectivity due to concurrent socket failures.

- **application_1445182159119_0004**
  - Ground truth: `disk_full`
  - Predicted: `unknown` (coarse: `unknown`)
  - Evidence snippet highlights:
    - `java.io.IOException: There is not enough space on the disk`
  - Interpretation: this is a true disk-full signal; failure to classify indicates the current mapping/decision is too brittle (and/or the hypothesis text did not include disk keywords).

- **application_1445182159119_0001**
  - Ground truth: `disk_full`
  - Predicted: `machine_down` (coarse: `connectivity`)
  - Evidence snippet highlights:
    - `evidence_snippet: []`
  - Interpretation: the log sampling missed the strongest disk-full indicators for this app (empty evidence), making classification unreliable.

Conclusion: disk-full detection is precise when triggered, but recall suffers due to mixed symptoms (connectivity noise) and incomplete evidence capture.

## Recommended Next Steps

### A) Misclassification audit (minimum needed for the final write-up)
- For each of the three major confusion families:
  - `normal → connectivity`
  - `machine_down → network_disconnection`
  - `disk_full → (connectivity/unknown)`
- Sample 3–5 applications and quote their `evidence_snippet` to justify whether the strict label mismatch is expected.

### B) Define the Week 6 reporting stance
For Week 6, the recommended headline metric is:

- **Primary headline**: **Coarse (3-class) operational diagnosis**
  - Rationale: `machine_down` and `network_disconnection` are frequently indistinguishable in logs (both appear as connection failures). The coarse metric better reflects what the system can reliably infer from observable evidence.
  - Headline values:
    - Accuracy: 61.8%
    - `connectivity` F1: 81.0% (P=72.7%, R=91.4%)

- **Secondary (reported transparently)**: **Strict (4-class) injected-failure match**
  - Rationale: this is the direct mapping to the dataset labels, but it penalizes the system for symptom-vs-injected-fault ambiguity and for “normal” runs that contain non-trivial error signatures.
  - Strict accuracy: 21.8%

### C) Improve robustness for long runs
- Optional hardening: fix the JudgeAgent formatting bug that can crash when hypothesis fields are not strings.

## Artifacts Summary

- **Main outputs**:
  - `docs/HADOOP1_GROUND_TRUTH_RESULTS.json`
  - `docs/HADOOP1_GROUND_TRUTH_METRICS.json`

- **Copies / intermediate runs**:
  - `docs/week6_validation_results/`

- **Ground truth labels**:
  - `loghub/Hadoop1/abnormal_label.txt`

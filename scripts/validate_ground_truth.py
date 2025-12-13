#!/usr/bin/env python3
"""
Ground Truth Validation Script

Validates RCA system outputs against known failure patterns and evidence.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any
import re
import sys
import argparse
from collections import Counter, defaultdict
import random
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.kg_retrieval import KGRetrievalAgent
from src.agents.rca_log_reasoner import LogFocusedReasoner
from src.agents.rca_kg_reasoner import KGFocusedReasoner
from src.agents.rca_hybrid_reasoner import HybridReasoner
from src.agents.judge_agent import JudgeAgent
from src.debate.debate_coordinator import DebateCoordinator

# Known Hadoop failure types (from README)
HADOOP_KNOWN_FAILURES = {
    'machine_down': {
        'description': 'Server turned off during execution',
        'expected_category': ['hardware', 'infrastructure', 'node failure'],
        'log_indicators': [
            'lost task tracker',
            'node failure',
            'tasktracker.*lost',
            'connection.*refused',
            'no response from',
            'failed to connect'
        ]
    },
    'network_disconnection': {
        'description': 'Server disconnected from network',
        'expected_category': ['network', 'connectivity', 'communication'],
        'log_indicators': [
            'connection refused',
            'timeout',
            'network.*error',
            'connection.*timeout',
            'unreachable',
            'connection.*lost'
        ]
    },
    'disk_full': {
        'description': 'Hard disk manually filled up',
        'expected_category': ['resource', 'storage', 'disk', 'space'],
        'log_indicators': [
            'no space left',
            'disk quota exceeded',
            'disk.*full',
            'out of space',
            'insufficient.*space',
            'cannot write'
        ]
    }
}

# Expected categories by system type
EXPECTED_CATEGORIES = {
    'HDFS': {
        'appropriate': ['configuration', 'network', 'disk', 'hardware', 'replication', 'block'],
        'common': ['configuration', 'network'],
        'rare': ['memory', 'application']
    },
    'Hadoop': {
        'appropriate': ['configuration', 'resource', 'network', 'task', 'job'],
        'common': ['configuration', 'resource', 'network'],
        'rare': ['storage']
    },
    'Spark': {
        'appropriate': ['memory', 'resource', 'configuration', 'executor', 'shuffle', 'security'],
        'common': ['memory', 'resource', 'configuration'],
        'rare': ['storage']
    }
}

class GroundTruthValidator:
    def __init__(self):
        self.results = []
        self.validation_scores = {}

        self._labels_by_app_id = {}
        
    def load_scenario_result(self, result_file: str) -> Dict:
        """Load a scenario result JSON file."""
        with open(result_file, 'r') as f:
            return json.load(f)

    def load_config(self) -> Dict[str, Any]:
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        kg_config = config.get('knowledge_graph', {})
        if kg_config.get('password') == '${NEO4J_PASSWORD}':
            kg_config['password'] = '1997Amaterasu'

        return config

    def load_hadoop1_labels(self, label_file: Path) -> Dict[str, str]:
        labels_by_app_id: Dict[str, str] = {}

        current_label = None
        label_map = {
            'normal': 'normal',
            'machine down': 'machine_down',
            'network disconnection': 'network_disconnection',
            'disk full': 'disk_full',
        }

        for raw_line in label_file.read_text(errors='ignore').splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.endswith(':') and not line.startswith('+'):
                key = line[:-1].strip().lower()
                current_label = label_map.get(key)
                continue

            if line.startswith('+'):
                if not current_label:
                    continue
                app_id = line[1:].strip()
                if app_id:
                    labels_by_app_id[app_id] = current_label

        self._labels_by_app_id = labels_by_app_id
        return labels_by_app_id

    def select_balanced_app_ids(
        self,
        per_class: int,
        seed: int = 42,
        classes: List[str] = None,
    ) -> List[str]:
        if classes is None:
            classes = ['normal', 'machine_down', 'network_disconnection', 'disk_full']

        by_label: Dict[str, List[str]] = defaultdict(list)
        for app_id, label in self._labels_by_app_id.items():
            by_label[label].append(app_id)

        rng = random.Random(seed)

        selected: List[str] = []
        for label in classes:
            candidates = by_label.get(label, [])
            rng.shuffle(candidates)
            selected.extend(candidates[:per_class])

        return selected

    def _coarse_failure_group(self, label: str) -> str:
        if label in {'machine_down', 'network_disconnection'}:
            return 'connectivity'
        if label in {'disk_full'}:
            return 'disk_full'
        if label in {'normal'}:
            return 'normal'
        return 'unknown'

    def _extract_application_ids(self, text: str) -> List[str]:
        if not text:
            return []

        app_ids = set(re.findall(r"application_\d+_\d+", text))
        for appattempt in re.findall(r"appattempt_(\d+_\d+)_\d+_\d+", text):
            app_ids.add(f"application_{appattempt}")

        return sorted(app_ids)

    def _load_hadoop1_application_raw_logs(
        self,
        app_id: str,
        max_lines: int = 2500,
        max_files: int = 6,
    ) -> str:
        app_dir = Path('loghub') / 'Hadoop1' / app_id
        if not app_dir.exists():
            raise FileNotFoundError(f"Application directory not found: {app_dir}")

        log_files = sorted(
            app_dir.glob('*.log'),
            key=lambda p: p.stat().st_size,
            reverse=True,
        )
        log_files = log_files[:max_files]

        keep_terms = (
            ' ERROR ',
            ' WARN ',
            ' Exception',
            ' exception',
            ' failed',
            ' Failed',
            ' timeout',
            ' Timeout',
            ' refused',
            ' Refused',
            ' unreachable',
            ' Unreachable',
            ' no space',
            ' No space',
        )

        selected: List[str] = []
        for f in log_files:
            try:
                with f.open('r', errors='ignore') as fp:
                    head = []
                    error_lines = []
                    for i, line in enumerate(fp):
                        if i < 120:
                            head.append(line.rstrip('\n'))

                        if any(t in line for t in keep_terms):
                            ln = line.rstrip('\n')
                            error_lines.append(ln)

                        if len(head) + len(error_lines) >= max_lines:
                            break

                selected.extend(head)
                selected.extend(error_lines)
            except Exception:
                continue

            if len(selected) >= max_lines:
                break

        raw_text = "\n".join(selected[:max_lines])
        return raw_text

    def _extract_evidence_snippet(self, raw_text: str, max_lines: int = 25) -> List[str]:
        if not raw_text:
            return []

        keep_re = re.compile(r"(\bERROR\b|\bWARN\b|Exception|failed|timeout|refused|unreachable|no space)", re.IGNORECASE)
        out = []
        for line in raw_text.splitlines():
            if keep_re.search(line):
                out.append(line)
                if len(out) >= max_lines:
                    break
        return out

    def _build_parsed_data_from_raw_text(self, raw_text: str) -> Dict[str, Any]:
        events = []
        entities = []
        error_messages = []

        component_seen = set()

        line_re = re.compile(
            r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+\s+(\w+)\s+\[[^\]]*\]\s+([^:]+):\s+(.*)$"
        )

        for raw_line in raw_text.splitlines():
            m = line_re.match(raw_line)
            if m:
                ts, level, component, message = m.groups()
            else:
                ts, level, component, message = "", "INFO", "", raw_line

            event = {
                "timestamp": ts,
                "level": level,
                "component": component,
                "message": message,
            }
            events.append(event)

            if component and component not in component_seen:
                entities.append({"type": "component", "value": component, "component": component})
                component_seen.add(component)

            if level in ['ERROR', 'FATAL', 'WARN'] or any(k in message.lower() for k in ['error', 'exception', 'failed', 'failure', 'fatal']):
                error_messages.append({
                    "timestamp": ts,
                    "level": level,
                    "component": component,
                    "message": message,
                })

        return {
            "raw_logs": raw_text,
            "events": events,
            "entities": entities,
            "error_messages": error_messages,
            "timeline": events,
        }

    def _run_rca_pipeline(self, parsed_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        kg_agent = KGRetrievalAgent(config=config)
        try:
            kg_data = kg_agent.process(parsed_data)
        except Exception:
            kg_data = {"similar_incidents": [], "entity_contexts": []}

        combined_data = {**parsed_data, **kg_data}

        log_reasoner = LogFocusedReasoner(config=config)
        kg_reasoner = KGFocusedReasoner(config=config)
        hybrid_reasoner = HybridReasoner(config=config)
        judge = JudgeAgent(config=config)

        coordinator = DebateCoordinator(
            log_reasoner=log_reasoner,
            kg_reasoner=kg_reasoner,
            hybrid_reasoner=hybrid_reasoner,
            judge=judge,
            max_rounds=3,
            convergence_threshold=5.0,
        )

        return coordinator.run_debate(combined_data)

    def _normalize_predicted_category(self, category: str, hypothesis_text: str) -> str:
        text = f"{category or ''} {hypothesis_text or ''}".lower()
        if any(k in text for k in ['disk', 'storage', 'no space', 'out of space']):
            return 'disk_full'
        if any(k in text for k in ['machine', 'node', 'hardware', 'tasktracker', 'datanode down']):
            return 'machine_down'
        if any(k in text for k in ['network', 'connect', 'timeout', 'unreachable', 'refused', 'forcibly closed', 'bad connect']):
            return 'network_disconnection'
        if 'normal' in text:
            return 'normal'
        return 'unknown'

    def _score_log_indicators(self, raw_text: str) -> Dict[str, int]:
        text = (raw_text or '').lower()
        scores: Dict[str, int] = {}
        for failure_type, info in HADOOP_KNOWN_FAILURES.items():
            score = 0
            for indicator in info.get('log_indicators', []):
                try:
                    score += len(re.findall(indicator.lower(), text))
                except re.error:
                    continue
            scores[failure_type] = score

        if scores.get('disk_full', 0) == 0:
            for extra in ['no space left', 'out of space', 'disk quota exceeded']:
                scores['disk_full'] += text.count(extra)

        return scores

    def _best_indicator_type(self, indicator_scores: Dict[str, int]) -> str:
        if not indicator_scores:
            return 'unknown'
        best = max(indicator_scores, key=indicator_scores.get)
        if indicator_scores.get(best, 0) <= 0:
            return 'unknown'
        return best

    def compute_metrics(
        self,
        rows: List[Dict[str, Any]],
        labels: List[str],
        pred_key: str = 'predicted_failure_type',
        gt_key: str = 'ground_truth',
    ) -> Dict[str, Any]:
        labels_all = list(labels)
        if 'unknown' not in labels_all:
            labels_all.append('unknown')

        labels_eval = [l for l in labels_all if l != 'unknown']

        confusion: Dict[str, Dict[str, int]] = {gt: {p: 0 for p in labels_all} for gt in labels_all}

        for r in rows:
            gt = r.get(gt_key, 'unknown')
            pred = r.get(pred_key, 'unknown')

            if gt not in labels_all:
                gt = 'unknown'
            if pred not in labels_all:
                pred = 'unknown'

            confusion[gt][pred] += 1

        per_class: Dict[str, Any] = {}
        total = 0
        correct = 0

        for cls in labels_eval:
            tp = confusion[cls][cls]
            fp = sum(confusion[gt][cls] for gt in labels_all if gt != cls)
            fn = sum(confusion[cls][p] for p in labels_all if p != cls)
            support = sum(confusion[cls].values())
            precision = (tp / (tp + fp)) if (tp + fp) else 0.0
            recall = (tp / (tp + fn)) if (tp + fn) else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
            per_class[cls] = {
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'support': support,
            }
            total += support
            correct += tp

        accuracy = (correct / total) if total else 0.0
        macro_precision = sum(per_class[c]['precision'] for c in labels_eval) / len(labels_eval)
        macro_recall = sum(per_class[c]['recall'] for c in labels_eval) / len(labels_eval)
        macro_f1 = sum(per_class[c]['f1'] for c in labels_eval) / len(labels_eval)

        unknown_pred = sum(confusion[gt]['unknown'] for gt in labels_all)

        return {
            'labels': labels_eval,
            'labels_all': labels_all,
            'accuracy': accuracy,
            'macro_avg': {
                'precision': macro_precision,
                'recall': macro_recall,
                'f1': macro_f1,
            },
            'per_class': per_class,
            'confusion': confusion,
            'total': total,
            'unknown_predictions': unknown_pred,
        }

    def _expected_failure_types_for_label(self, label: str) -> List[str]:
        if not label:
            return []
        if label in {'machine_down', 'network_disconnection', 'disk_full', 'normal'}:
            return [label]
        return []

    def validate_hadoop1_applications(
        self,
        app_ids: List[str],
        max_lines: int = 2500,
        max_files: int = 6,
    ) -> List[Dict[str, Any]]:
        config = self.load_config()

        out = []
        for app_id in app_ids:
            gt_label = self._labels_by_app_id.get(app_id, 'unknown')
            raw_text = self._load_hadoop1_application_raw_logs(app_id, max_lines=max_lines, max_files=max_files)
            evidence_snippet = self._extract_evidence_snippet(raw_text)
            indicator_scores = self._score_log_indicators(raw_text)
            indicator_best = self._best_indicator_type(indicator_scores)
            parsed_data = self._build_parsed_data_from_raw_text(raw_text)
            results = self._run_rca_pipeline(parsed_data, config)

            final = results.get('final_hypothesis') or {}
            predicted_category = final.get('category', '')
            predicted_text = final.get('hypothesis', '')
            predicted_type = self._normalize_predicted_category(predicted_category, predicted_text)

            predicted_final = predicted_type
            if predicted_final == 'unknown' and indicator_best != 'unknown':
                predicted_final = indicator_best

            expected_types = self._expected_failure_types_for_label(gt_label)
            strict_match = predicted_final in expected_types

            row = {
                'dataset': 'Hadoop1',
                'application_id': app_id,
                'ground_truth': gt_label,
                'predicted_category': predicted_category,
                'predicted_failure_type': predicted_final,
                'predicted_failure_type_from_hypothesis': predicted_type,
                'predicted_failure_type_from_indicators': indicator_best,
                'ground_truth_coarse': self._coarse_failure_group(gt_label),
                'predicted_failure_type_coarse': self._coarse_failure_group(predicted_final),
                'strict_match': strict_match,
                'final_score': final.get('judge_score', None),
                'confidence': final.get('confidence', None),
                'hypothesis': predicted_text,
                'indicator_scores': indicator_scores,
                'evidence_snippet': evidence_snippet,
            }
            out.append(row)
            self.results.append(row)

        return out
    
    def load_logs(self, dataset: str, scenario_id: int) -> pd.DataFrame:
        """Load structured logs for a scenario."""
        log_file = f"loghub/{dataset}/{dataset}_2k.log_structured.csv"
        df = pd.read_csv(log_file)
        # For now, return first 100 events (our scenarios use 100 events)
        start_idx = (scenario_id - 1) * 100
        end_idx = start_idx + 100
        return df.iloc[start_idx:end_idx]
    
    def identify_hadoop_failure_type(self, logs: pd.DataFrame) -> Tuple[str, float]:
        """
        Identify which Hadoop failure type based on log indicators.
        Returns (failure_type, confidence)
        """
        log_text = ' '.join(logs['Content'].astype(str).tolist()).lower()
        
        scores = {}
        for failure_type, info in HADOOP_KNOWN_FAILURES.items():
            score = 0
            for indicator in info['log_indicators']:
                # Use regex to find matches
                matches = len(re.findall(indicator.lower(), log_text))
                score += matches
            scores[failure_type] = score
        
        # Get failure type with highest score
        if max(scores.values()) == 0:
            return 'unknown', 0.0
        
        best_type = max(scores, key=scores.get)
        confidence = scores[best_type] / sum(scores.values()) if sum(scores.values()) > 0 else 0.0
        
        return best_type, confidence
    
    def check_category_match(self, hypothesis: str, expected_categories: List[str]) -> bool:
        """Check if hypothesis category matches expected categories."""
        hypothesis_lower = hypothesis.lower()
        for category in expected_categories:
            if category.lower() in hypothesis_lower:
                return True
        return False
    
    def calculate_plausibility_score(self, dataset: str, hypothesis: str) -> Tuple[int, str]:
        """
        Calculate plausibility score (1-5) based on expected categories.
        Returns (score, reasoning)
        """
        hypothesis_lower = hypothesis.lower()
        expected = EXPECTED_CATEGORIES[dataset]
        
        # Check if hypothesis contains appropriate categories
        appropriate_found = any(cat in hypothesis_lower for cat in expected['appropriate'])
        common_found = any(cat in hypothesis_lower for cat in expected['common'])
        rare_found = any(cat in hypothesis_lower for cat in expected['rare'])
        
        if common_found:
            return 5, f"Hypothesis mentions common {dataset} failure category"
        elif appropriate_found and not rare_found:
            return 4, f"Hypothesis mentions appropriate {dataset} category"
        elif appropriate_found and rare_found:
            return 3, f"Hypothesis mentions rare but possible {dataset} category"
        elif rare_found:
            return 2, f"Hypothesis mentions unlikely category for {dataset}"
        else:
            return 1, f"Hypothesis category doesn't match expected {dataset} patterns"
    
    def extract_evidence_from_logs(self, logs: pd.DataFrame, hypothesis: str) -> List[str]:
        """Extract log evidence that supports or contradicts hypothesis."""
        evidence = []
        hypothesis_lower = hypothesis.lower()
        
        # Extract key terms from hypothesis
        key_terms = []
        if 'configuration' in hypothesis_lower or 'config' in hypothesis_lower:
            key_terms.extend(['config', 'parameter', 'setting'])
        if 'network' in hypothesis_lower:
            key_terms.extend(['network', 'connection', 'timeout', 'refused'])
        if 'resource' in hypothesis_lower or 'memory' in hypothesis_lower:
            key_terms.extend(['memory', 'resource', 'space', 'allocation'])
        if 'disk' in hypothesis_lower or 'storage' in hypothesis_lower:
            key_terms.extend(['disk', 'storage', 'space', 'quota'])
        
        # Search logs for evidence
        for _, row in logs.iterrows():
            content = str(row['Content']).lower()
            for term in key_terms:
                if term in content:
                    evidence.append(row['Content'])
                    break
        
        return evidence[:10]  # Return top 10 evidence items
    
    def calculate_evidence_support(self, logs: pd.DataFrame, hypothesis: str) -> Tuple[int, str]:
        """
        Calculate evidence support score (1-3).
        Returns (score, reasoning)
        """
        evidence = self.extract_evidence_from_logs(logs, hypothesis)
        
        if len(evidence) >= 5:
            return 3, f"Strong evidence support ({len(evidence)} supporting log entries)"
        elif len(evidence) >= 2:
            return 2, f"Medium evidence support ({len(evidence)} supporting log entries)"
        else:
            return 1, f"Weak evidence support ({len(evidence)} supporting log entries)"
    
    def validate_hadoop_scenario(self, scenario_id: int) -> Dict:
        """Validate a Hadoop scenario against known failure types."""
        # Load result
        result_file = f"hadoop_scenario_{scenario_id}_results.json"
        result = self.load_scenario_result(result_file)
        
        # Load logs
        logs = self.load_logs('Hadoop', scenario_id)
        
        # Identify failure type
        failure_type, confidence = self.identify_hadoop_failure_type(logs)
        
        # Check if hypothesis matches
        hypothesis = result['final_hypothesis']
        expected_categories = HADOOP_KNOWN_FAILURES.get(failure_type, {}).get('expected_category', [])
        category_match = self.check_category_match(hypothesis, expected_categories)
        
        # Calculate plausibility
        plausibility_score, plausibility_reason = self.calculate_plausibility_score('Hadoop', hypothesis)
        
        # Calculate evidence support
        evidence_score, evidence_reason = self.calculate_evidence_support(logs, hypothesis)
        
        # Extract evidence
        evidence = self.extract_evidence_from_logs(logs, hypothesis)
        
        return {
            'scenario_id': scenario_id,
            'dataset': 'Hadoop',
            'hypothesis': hypothesis,
            'final_score': result['final_score'],
            'identified_failure_type': failure_type,
            'failure_confidence': confidence,
            'expected_categories': expected_categories,
            'category_match': category_match,
            'plausibility_score': plausibility_score,
            'plausibility_reason': plausibility_reason,
            'evidence_support_score': evidence_score,
            'evidence_support_reason': evidence_reason,
            'evidence_count': len(evidence),
            'evidence_sample': evidence[:3]
        }
    
    def validate_other_scenario(self, dataset: str, scenario_id: int) -> Dict:
        """Validate HDFS or Spark scenario (no known failure types)."""
        # Load result
        if dataset == 'HDFS':
            result_file = f"hdfs_scenario_{scenario_id}_results_test#1.json"
        else:
            result_file = f"spark_scenario_{scenario_id}_results.json"
        
        result = self.load_scenario_result(result_file)
        
        # Load logs
        logs = self.load_logs(dataset, scenario_id)
        
        # Calculate plausibility
        hypothesis = result['final_hypothesis']
        plausibility_score, plausibility_reason = self.calculate_plausibility_score(dataset, hypothesis)
        
        # Calculate evidence support
        evidence_score, evidence_reason = self.calculate_evidence_support(logs, hypothesis)
        
        # Extract evidence
        evidence = self.extract_evidence_from_logs(logs, hypothesis)
        
        return {
            'scenario_id': scenario_id,
            'dataset': dataset,
            'hypothesis': hypothesis,
            'final_score': result['final_score'],
            'plausibility_score': plausibility_score,
            'plausibility_reason': plausibility_reason,
            'evidence_support_score': evidence_score,
            'evidence_support_reason': evidence_reason,
            'evidence_count': len(evidence),
            'evidence_sample': evidence[:3]
        }
    
    def validate_all_scenarios(self):
        """Validate all 9 scenarios."""
        print("\n" + "="*70)
        print("GROUND TRUTH VALIDATION")
        print("="*70 + "\n")
        
        # Validate Hadoop scenarios (with known failures)
        print("Validating Hadoop scenarios (known failure types)...")
        for i in range(1, 4):
            try:
                result = self.validate_hadoop_scenario(i)
                self.results.append(result)
                print(f"  ✓ Hadoop Scenario {i}: {result['identified_failure_type']} "
                      f"(confidence: {result['failure_confidence']:.2f})")
            except Exception as e:
                print(f"  ✗ Hadoop Scenario {i}: Error - {e}")
        
        # Validate HDFS scenarios
        print("\nValidating HDFS scenarios (plausibility-based)...")
        for i in range(1, 4):
            try:
                result = self.validate_other_scenario('HDFS', i)
                self.results.append(result)
                print(f"  ✓ HDFS Scenario {i}: Plausibility {result['plausibility_score']}/5")
            except Exception as e:
                print(f"  ✗ HDFS Scenario {i}: Error - {e}")
        
        # Validate Spark scenarios
        print("\nValidating Spark scenarios (plausibility-based)...")
        for i in range(1, 4):
            try:
                result = self.validate_other_scenario('Spark', i)
                self.results.append(result)
                print(f"  ✓ Spark Scenario {i}: Plausibility {result['plausibility_score']}/5")
            except Exception as e:
                print(f"  ✗ Spark Scenario {i}: Error - {e}")
    
    def generate_report(self):
        """Generate validation report."""
        print("\n" + "="*70)
        print("VALIDATION SUMMARY")
        print("="*70 + "\n")
        
        # Hadoop accuracy
        hadoop_results = [r for r in self.results if r['dataset'] == 'Hadoop']
        if hadoop_results:
            hadoop_matches = sum(1 for r in hadoop_results if r.get('category_match', False))
            hadoop_accuracy = hadoop_matches / len(hadoop_results) * 100
            print(f"Hadoop Known Failure Accuracy: {hadoop_accuracy:.1f}% ({hadoop_matches}/{len(hadoop_results)})")
            
            for r in hadoop_results:
                match_symbol = "✅" if r.get('category_match', False) else "❌"
                print(f"  {match_symbol} Scenario {r['scenario_id']}: {r['identified_failure_type']} "
                      f"(confidence: {r['failure_confidence']:.2f})")
        
        # Overall plausibility
        avg_plausibility = sum(r['plausibility_score'] for r in self.results) / len(self.results)
        print(f"\nOverall Plausibility Score: {avg_plausibility:.2f}/5.00")
        
        # Overall evidence support
        avg_evidence = sum(r['evidence_support_score'] for r in self.results) / len(self.results)
        print(f"Overall Evidence Support: {avg_evidence:.2f}/3.00")
        
        # By dataset
        print("\nBy Dataset:")
        for dataset in ['HDFS', 'Hadoop', 'Spark']:
            dataset_results = [r for r in self.results if r['dataset'] == dataset]
            if dataset_results:
                avg_plaus = sum(r['plausibility_score'] for r in dataset_results) / len(dataset_results)
                avg_evid = sum(r['evidence_support_score'] for r in dataset_results) / len(dataset_results)
                print(f"  {dataset}: Plausibility {avg_plaus:.2f}/5, Evidence {avg_evid:.2f}/3")
        
        # Save detailed results
        output_file = 'docs/GROUND_TRUTH_VALIDATION_RESULTS.json'
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✓ Detailed results saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['hadoop1', 'legacy'], default='hadoop1')
    parser.add_argument('--max-apps', type=int, default=3)
    parser.add_argument('--balanced-per-class', type=int, default=0)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--apps', type=str, default='')
    parser.add_argument('--max-lines', type=int, default=2500)
    parser.add_argument('--max-files', type=int, default=6)
    args = parser.parse_args()

    validator = GroundTruthValidator()

    if args.mode == 'legacy':
        validator.validate_all_scenarios()
        validator.generate_report()

        print("\n" + "="*70)
        print("✓ VALIDATION COMPLETE!")
        print("="*70 + "\n")
        return

    labels = validator.load_hadoop1_labels(Path('loghub') / 'Hadoop1' / 'abnormal_label.txt')
    if args.apps.strip():
        app_ids = [a.strip() for a in args.apps.split(',') if a.strip()]
    elif args.all:
        app_ids = sorted(labels.keys())
    elif args.balanced_per_class and args.balanced_per_class > 0:
        app_ids = validator.select_balanced_app_ids(per_class=args.balanced_per_class, seed=args.seed)
    else:
        app_ids = sorted(labels.keys())[: max(1, args.max_apps)]

    results = validator.validate_hadoop1_applications(app_ids, max_lines=args.max_lines, max_files=args.max_files)

    strict_labels = ['normal', 'machine_down', 'network_disconnection', 'disk_full']
    strict_metrics = validator.compute_metrics(
        results,
        labels=strict_labels,
        pred_key='predicted_failure_type',
        gt_key='ground_truth',
    )

    coarse_labels = ['normal', 'connectivity', 'disk_full']
    coarse_metrics = validator.compute_metrics(
        results,
        labels=coarse_labels,
        pred_key='predicted_failure_type_coarse',
        gt_key='ground_truth_coarse',
    )

    print("\n" + "="*70)
    print("HADOOP1 GROUND TRUTH VALIDATION")
    print("="*70)
    print(f"Applications evaluated: {len(results)}")
    print(f"Sampling: apps={len(app_ids)} balanced_per_class={args.balanced_per_class} all={args.all} seed={args.seed}")

    print("\nSTRICT (4-class) metrics:")
    print(f"  Accuracy: {strict_metrics['accuracy']*100:.1f}%")
    print(f"  Macro Precision/Recall/F1: {strict_metrics['macro_avg']['precision']*100:.1f}% / "
          f"{strict_metrics['macro_avg']['recall']*100:.1f}% / {strict_metrics['macro_avg']['f1']*100:.1f}%")
    for cls, stats in strict_metrics['per_class'].items():
        print(f"  {cls}: P={stats['precision']*100:.1f}% R={stats['recall']*100:.1f}% F1={stats['f1']*100:.1f}% (n={stats['support']})")

    print("\nCOARSE (3-class) metrics:")
    print(f"  Accuracy: {coarse_metrics['accuracy']*100:.1f}%")
    print(f"  Macro Precision/Recall/F1: {coarse_metrics['macro_avg']['precision']*100:.1f}% / "
          f"{coarse_metrics['macro_avg']['recall']*100:.1f}% / {coarse_metrics['macro_avg']['f1']*100:.1f}%")
    for cls, stats in coarse_metrics['per_class'].items():
        print(f"  {cls}: P={stats['precision']*100:.1f}% R={stats['recall']*100:.1f}% F1={stats['f1']*100:.1f}% (n={stats['support']})")

    output_file = Path('docs') / 'HADOOP1_GROUND_TRUTH_RESULTS.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open('w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Detailed results saved to: {output_file}")

    metrics_file = Path('docs') / 'HADOOP1_GROUND_TRUTH_METRICS.json'
    with metrics_file.open('w') as f:
        json.dump({
            'strict': strict_metrics,
            'coarse': coarse_metrics,
            'args': {
                'mode': args.mode,
                'max_apps': args.max_apps,
                'balanced_per_class': args.balanced_per_class,
                'seed': args.seed,
                'all': args.all,
                'apps': args.apps,
                'max_lines': args.max_lines,
                'max_files': args.max_files,
            }
        }, f, indent=2)
    print(f"✓ Metrics saved to: {metrics_file}")

    print("\n" + "="*70)
    print("✓ VALIDATION COMPLETE!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()

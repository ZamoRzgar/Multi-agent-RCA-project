#!/usr/bin/env python3
"""
HDFS_v1 Dataset Validation Script

Validates RCA system outputs against HDFS_v1 ground truth labels.
Binary classification: Normal vs Anomaly for HDFS block operations.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple
import re
import sys
import argparse
from collections import defaultdict
import random
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.base_agent import BaseAgent
from src.agents.kg_retrieval import KGRetrievalAgent
from src.agents.rca_log_reasoner import LogFocusedReasoner
from src.agents.rca_kg_reasoner import KGFocusedReasoner
from src.agents.rca_hybrid_reasoner import HybridReasoner
from src.agents.judge_agent import JudgeAgent
from src.debate.debate_coordinator import DebateCoordinator

# HDFS failure types (binary classification)
HDFS_LABELS = {
    'Normal': {
        'description': 'Block operations completed successfully',
        'keywords': ['normal', 'success', 'healthy', 'completed', 'no error'],
    },
    'Anomaly': {
        'description': 'Block operations failed or encountered errors',
        'keywords': ['anomaly', 'error', 'failure', 'exception', 'timeout', 'failed'],
    }
}

# Event templates for reference (from HDFS.log_templates.csv)
HDFS_EVENT_TEMPLATES = {
    'E1': 'Adding an already existing block',
    'E2': 'Verification succeeded',
    'E3': 'Served block',
    'E4': 'Got exception while serving',
    'E5': 'Receiving block',
    'E6': 'Received block with size',
    'E7': 'writeBlock received exception',
    'E8': 'PacketResponder Interrupted',
    'E9': 'Received block of size from',
    'E10': 'PacketResponder Exception',
    'E11': 'PacketResponder terminating',
    'E12': 'Exception writing block to mirror',
    'E13': 'Receiving empty packet',
    'E14': 'Exception in receiveBlock',
    'E15': 'Changing block file offset',
    'E16': 'Transmitted block',
    'E17': 'Failed to transfer',
    'E18': 'Starting thread to transfer block',
    'E19': 'Reopen Block',
    'E20': 'Unexpected error trying to delete block',
    'E21': 'Deleting block',
    'E22': 'NameSystem allocateBlock',
    'E23': 'NameSystem delete added to invalidSet',
    'E24': 'Removing block from neededReplications',
    'E25': 'Ask to replicate',
    'E26': 'NameSystem addStoredBlock blockMap updated',
    'E27': 'Redundant addStoredBlock request',
    'E28': 'addStoredBlock request but does not belong to file',
    'E29': 'PendingReplicationMonitor timed out',
}

# Error-indicating events
ERROR_EVENTS = {'E4', 'E7', 'E8', 'E10', 'E12', 'E13', 'E14', 'E17', 'E19', 'E20', 'E27', 'E28', 'E29'}


class HDFSSingleAgentBaseline(BaseAgent):
    """Single-agent baseline with HDFS-specific prompts."""
    
    def __init__(self, model: str = '', temperature: float = 0.3, max_tokens: int = 1400, **kwargs):
        super().__init__(
            name='HDFSSingleAgent',
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        if model:
            self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt(input_data)
        response = self._call_llm(prompt)
        parsed = self._parse_response(response)
        
        hypothesis = parsed.get('hypothesis', '') or ''
        if not hypothesis and response:
            hypothesis = response.strip()
        category = parsed.get('category', '') or 'unknown'
        
        return {
            'hypothesis': hypothesis,
            'category': category,
            'confidence': parsed.get('confidence', None),
            'suggested_resolution': parsed.get('suggested_resolution', ''),
            'source': 'single_agent',
            'raw_response': response,
        }

    def _build_prompt(self, input_data: Dict[str, Any]) -> str:
        raw_logs = input_data.get('raw_logs', '') or ''
        raw_excerpt = raw_logs[:12000]

        errors = input_data.get('error_messages', []) or []
        error_lines = []
        for e in errors[:40]:
            msg = e.get('message', '') if isinstance(e, dict) else str(e)
            if msg:
                error_lines.append(f"- {msg}")

        entities = input_data.get('entities', []) or []
        entity_vals = []
        for ent in entities[:30]:
            if isinstance(ent, dict):
                v = ent.get('value') or ent.get('component') or ''
                if v:
                    entity_vals.append(str(v))
            else:
                entity_vals.append(str(ent))

        entity_text = ', '.join(entity_vals[:30])
        error_text = '\n'.join(error_lines) if error_lines else '- (none)'
        
        event_sequence = input_data.get('event_sequence', '')

        return f"""You are an SRE analyst specializing in Hadoop HDFS distributed file system.
Given HDFS DataNode and NameNode logs for a specific block operation, determine if this is a Normal or Anomaly case.

IMPORTANT: You must classify the block operation into ONE of these categories:
- Normal: Block operations completed successfully (receiving, storing, serving, replicating blocks worked correctly)
- Anomaly: Block operations failed or encountered errors (exceptions, timeouts, failed transfers, corrupted blocks)

HDFS ERROR INDICATORS (suggest Anomaly):
- "Exception" in any form (writeBlock exception, PacketResponder Exception, receiveBlock exception)
- "Failed to transfer" or "Failed to replicate"
- "timeout" or "timed out"
- "Unexpected error" or "error trying to delete"
- "Interrupted" (PacketResponder Interrupted)
- "does not belong to any file"
- Multiple retries or reopening blocks

HDFS NORMAL INDICATORS (suggest Normal):
- "Verification succeeded"
- "Served block" without errors
- "Received block of size" (successful reception)
- "Transmitted block" (successful transfer)
- "blockMap updated" (successful storage)
- Clean block lifecycle: allocate -> receive -> store -> serve -> delete

EXAMPLES:
Example 1 - Anomaly:
Log: "writeBlock blk_123 received exception java.io.IOException... PacketResponder Exception... Failed to transfer"
Answer: {{"hypothesis": "Block write operation failed with I/O exception during packet response", "category": "Anomaly", "confidence": 0.9}}

Example 2 - Normal:
Log: "Receiving block blk_456... Received block of size 65536... blockMap updated... Served block to client"
Answer: {{"hypothesis": "Block operations completed successfully - received, stored, and served without errors", "category": "Normal", "confidence": 0.95}}

Example 3 - Anomaly:
Log: "PendingReplicationMonitor timed out block blk_789... Unexpected error trying to delete block"
Answer: {{"hypothesis": "Block replication timed out and deletion failed", "category": "Anomaly", "confidence": 0.85}}

Now analyze these HDFS logs and return ONLY a JSON object:
{{"hypothesis": "...", "category": "Normal or Anomaly", "confidence": 0.0-1.0, "suggested_resolution": "..."}}

Block ID: {input_data.get('block_id', 'unknown')}
Event sequence: {event_sequence if event_sequence else '(not available)'}

Known HDFS components: {entity_text if entity_text else '(none)'}

Error-like messages:
{error_text}

Log excerpt (truncated):
{raw_excerpt}"""

    def _parse_response(self, text: str) -> Dict[str, Any]:
        if not text:
            return {}
        cleaned = text.strip()
        m = re.search(r"\{.*\}", cleaned, re.S)
        payload = m.group(0) if m else cleaned
        try:
            obj = json.loads(payload)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

        out: Dict[str, Any] = {}
        hyp_m = re.search(r"hypothesis\s*[:=]\s*(.*)", cleaned, re.I)
        if hyp_m:
            out['hypothesis'] = hyp_m.group(1).strip().strip('"')
        cat_m = re.search(r"category\s*[:=]\s*(.*)", cleaned, re.I)
        if cat_m:
            out['category'] = cat_m.group(1).strip().strip('"')
        conf_m = re.search(r"confidence\s*[:=]\s*([0-9.]+)", cleaned, re.I)
        if conf_m:
            try:
                out['confidence'] = float(conf_m.group(1))
            except Exception:
                pass
        return out


class HDFSRAGBaseline(BaseAgent):
    """RAG baseline with HDFS-specific prompts and KG retrieval."""
    
    def __init__(self, model: str = '', temperature: float = 0.3, max_tokens: int = 2000, **kwargs):
        super().__init__(
            name='HDFSRAG',
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        if model:
            self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        self.kg_retrieval = None
        try:
            config = kwargs.get('config', {})
            self.kg_retrieval = KGRetrievalAgent(config=config)
        except Exception as e:
            print(f"Warning: Could not initialize KG for RAG: {e}")

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        retrieved_context = self._retrieve_context(input_data)
        prompt = self._build_prompt(input_data, retrieved_context)
        response = self._call_llm(prompt)
        parsed = self._parse_response(response)
        
        hypothesis = parsed.get('hypothesis', '') or ''
        if not hypothesis and response:
            hypothesis = response.strip()
        category = parsed.get('category', '') or 'unknown'
        
        return {
            'hypothesis': hypothesis,
            'category': category,
            'confidence': parsed.get('confidence', None),
            'suggested_resolution': parsed.get('suggested_resolution', ''),
            'source': 'rag_baseline',
            'raw_response': response,
            'retrieved_incidents': len(retrieved_context.get('similar_incidents', [])),
        }

    def _retrieve_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.kg_retrieval:
            return {'similar_incidents': [], 'entity_context': {}}
        try:
            kg_facts = self.kg_retrieval.process(input_data)
            return kg_facts
        except Exception as e:
            print(f"Warning: KG retrieval failed: {e}")
            return {'similar_incidents': [], 'entity_context': {}}

    def _build_prompt(self, input_data: Dict[str, Any], retrieved_context: Dict[str, Any]) -> str:
        raw_logs = input_data.get('raw_logs', '') or ''
        raw_excerpt = raw_logs[:10000]

        errors = input_data.get('error_messages', []) or []
        error_lines = []
        for e in errors[:40]:
            msg = e.get('message', '') if isinstance(e, dict) else str(e)
            if msg:
                error_lines.append(f"- {msg}")

        entities = input_data.get('entities', [])[:30]
        entity_vals = []
        for ent in entities:
            if isinstance(ent, dict):
                v = ent.get('value') or ent.get('component') or ''
                if v:
                    entity_vals.append(str(v))
            else:
                entity_vals.append(str(ent))
        entity_text = ', '.join(entity_vals)
        error_text = '\n'.join(error_lines) if error_lines else '- (none)'

        similar_incidents = retrieved_context.get('similar_incidents', [])
        retrieved_text = self._format_retrieved_incidents(similar_incidents)

        return f"""You are an SRE analyst specializing in Hadoop HDFS. Given HDFS logs and similar historical incidents, determine if this is Normal or Anomaly.

Return ONLY a JSON object: {{"hypothesis": "...", "category": "Normal or Anomaly", "confidence": 0.0-1.0, "suggested_resolution": "..."}}

=== SIMILAR HISTORICAL INCIDENTS (from knowledge base) ===
{retrieved_text}

=== CURRENT INCIDENT ===
Block ID: {input_data.get('block_id', 'unknown')}
Known components: {entity_text if entity_text else '(none)'}

Error messages:
{error_text}

Log excerpt:
{raw_excerpt}"""

    def _format_retrieved_incidents(self, incidents: List[Dict[str, Any]]) -> str:
        if not incidents:
            return "(No similar historical incidents found)"
        
        lines = []
        for i, inc in enumerate(incidents[:5], 1):
            incident_id = inc.get('incident_id', 'unknown')
            dataset = inc.get('dataset', 'unknown')
            root_cause = inc.get('root_cause', 'unknown')
            hypothesis = inc.get('hypothesis', '')
            
            lines.append(f"Incident {i}: [{dataset}] {incident_id}")
            lines.append(f"  Root Cause: {root_cause}")
            if hypothesis:
                lines.append(f"  Hypothesis: {hypothesis[:200]}...")
            lines.append("")
        
        return '\n'.join(lines)

    def _parse_response(self, text: str) -> Dict[str, Any]:
        if not text:
            return {}
        cleaned = text.strip()
        m = re.search(r"\{.*\}", cleaned, re.S)
        payload = m.group(0) if m else cleaned
        try:
            obj = json.loads(payload)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
        return {}


class HDFSValidator:
    """Validator for HDFS_v1 dataset."""
    
    def __init__(self, hdfs_root: str = 'loghub/HDFS_v1'):
        self.hdfs_root = Path(hdfs_root)
        self._labels_by_block_id: Dict[str, str] = {}
        self._event_traces: Dict[str, str] = {}
        self._raw_log_index: Dict[str, List[int]] = {}  # block_id -> line offsets
        
    def load_config(self) -> Dict[str, Any]:
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        kg_config = config.get('knowledge_graph', {})
        if kg_config.get('password') == '${NEO4J_PASSWORD}':
            kg_config['password'] = '1997Amaterasu'
        
        return config

    def load_labels(self) -> Dict[str, str]:
        """Load anomaly labels from CSV."""
        label_file = self.hdfs_root / 'preprocessed' / 'anomaly_label.csv'
        df = pd.read_csv(label_file)
        
        for _, row in df.iterrows():
            block_id = row['BlockId']
            label = row['Label']
            # Normalize: Normal/Anomaly
            if label == 'Normal':
                self._labels_by_block_id[block_id] = 'Normal'
            else:
                self._labels_by_block_id[block_id] = 'Anomaly'
        
        print(f"Loaded {len(self._labels_by_block_id)} block labels")
        print(f"  Normal: {sum(1 for v in self._labels_by_block_id.values() if v == 'Normal')}")
        print(f"  Anomaly: {sum(1 for v in self._labels_by_block_id.values() if v == 'Anomaly')}")
        
        return self._labels_by_block_id

    def load_event_traces(self) -> Dict[str, str]:
        """Load event traces for blocks."""
        traces_file = self.hdfs_root / 'preprocessed' / 'Event_traces.csv'
        df = pd.read_csv(traces_file)
        
        for _, row in df.iterrows():
            block_id = row['BlockId']
            features = row.get('Features', '')
            self._event_traces[block_id] = str(features)
        
        print(f"Loaded {len(self._event_traces)} event traces")
        return self._event_traces

    def select_balanced_blocks(
        self,
        n_normal: int = 50,
        n_anomaly: int = 50,
        seed: int = 42,
    ) -> List[str]:
        """Select balanced sample of normal and anomaly blocks."""
        normal_blocks = [b for b, l in self._labels_by_block_id.items() if l == 'Normal']
        anomaly_blocks = [b for b, l in self._labels_by_block_id.items() if l == 'Anomaly']
        
        rng = random.Random(seed)
        rng.shuffle(normal_blocks)
        rng.shuffle(anomaly_blocks)
        
        selected = normal_blocks[:n_normal] + anomaly_blocks[:n_anomaly]
        rng.shuffle(selected)
        
        print(f"Selected {len(selected)} blocks: {n_normal} normal, {n_anomaly} anomaly")
        return selected

    def extract_block_logs(self, block_id: str, max_lines: int = 500) -> str:
        """Extract raw logs for a specific block from HDFS.log."""
        log_file = self.hdfs_root / 'HDFS.log'
        
        lines = []
        with open(log_file, 'r', errors='ignore') as f:
            for line in f:
                if block_id in line:
                    lines.append(line.strip())
                    if len(lines) >= max_lines:
                        break
        
        return '\n'.join(lines)

    def build_parsed_data(self, block_id: str, raw_logs: str) -> Dict[str, Any]:
        """Build parsed data structure from raw logs."""
        events = []
        entities = []
        error_messages = []
        
        component_seen = set()
        
        # HDFS log format: YYMMDD HHMMSS PID LEVEL component: message
        log_pattern = re.compile(r'^(\d{6})\s+(\d{6})\s+(\d+)\s+(\w+)\s+([^:]+):\s*(.*)$')
        
        for raw_line in raw_logs.splitlines():
            m = log_pattern.match(raw_line)
            if m:
                date, time, pid, level, component, message = m.groups()
                ts = f"{date} {time}"
            else:
                ts, level, component, message = "", "INFO", "", raw_line
            
            event = {
                "timestamp": ts,
                "level": level,
                "component": component.strip(),
                "message": message,
            }
            events.append(event)
            
            # Extract components as entities
            if component and component.strip() not in component_seen:
                comp = component.strip()
                component_seen.add(comp)
                entities.append({
                    "type": "hdfs_component",
                    "value": comp,
                    "component": comp,
                })
            
            # Collect error messages
            if level.upper() in ('ERROR', 'WARN', 'WARNING', 'FATAL') or \
               any(kw in message.lower() for kw in ['exception', 'error', 'failed', 'timeout']):
                error_messages.append({
                    "level": level,
                    "component": component.strip(),
                    "message": message,
                })
        
        # Get event sequence if available
        event_sequence = self._event_traces.get(block_id, '')
        
        return {
            "block_id": block_id,
            "raw_logs": raw_logs,
            "events": events,
            "entities": entities,
            "error_messages": error_messages,
            "timeline": events,
            "event_sequence": event_sequence,
        }

    def normalize_prediction(self, category: str, hypothesis: str) -> str:
        """Normalize LLM prediction to HDFS label."""
        text = f"{category or ''} {hypothesis or ''}".lower()
        
        # Direct category match
        category_clean = (category or '').strip()
        if category_clean in ('Normal', 'Anomaly'):
            return category_clean
        if category_clean.lower() == 'normal':
            return 'Normal'
        if category_clean.lower() == 'anomaly':
            return 'Anomaly'
        
        # Keyword-based detection
        anomaly_keywords = [
            'anomaly', 'error', 'exception', 'failed', 'failure', 'timeout',
            'timed out', 'interrupted', 'unexpected', 'corrupt', 'invalid',
            'problem', 'issue', 'fault', 'abnormal'
        ]
        normal_keywords = [
            'normal', 'success', 'successful', 'healthy', 'completed',
            'no error', 'no issue', 'working', 'correct', 'valid'
        ]
        
        anomaly_score = sum(1 for kw in anomaly_keywords if kw in text)
        normal_score = sum(1 for kw in normal_keywords if kw in text)
        
        if anomaly_score > normal_score:
            return 'Anomaly'
        elif normal_score > anomaly_score:
            return 'Normal'
        
        return 'unknown'

    def run_rca_pipeline(self, parsed_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Run full multi-agent RCA pipeline."""
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

    def validate_blocks(
        self,
        block_ids: List[str],
        max_lines: int = 500,
        pipeline: str = 'multi_agent',
        model: str = '',
    ) -> List[Dict[str, Any]]:
        """Validate HDFS blocks against ground truth."""
        config = self.load_config()
        results = []
        
        for idx, block_id in enumerate(block_ids, 1):
            gt_label = self._labels_by_block_id.get(block_id, 'unknown')
            
            print(f"[{idx}/{len(block_ids)}] Processing {block_id[:20]}... (GT: {gt_label})")
            
            try:
                raw_logs = self.extract_block_logs(block_id, max_lines=max_lines)
                if not raw_logs.strip():
                    print(f"  ⚠ No logs found for block, skipping")
                    continue
            except Exception as e:
                print(f"  ⚠ Error extracting logs: {e}")
                continue
            
            parsed_data = self.build_parsed_data(block_id, raw_logs)
            
            if pipeline == 'single_agent':
                agent = HDFSSingleAgentBaseline(model=model)
                response = agent.process(parsed_data)
                hypothesis = response.get('hypothesis', '')
                category = response.get('category', '')
                confidence = response.get('confidence', 0.5) or 0.5
                final_score = confidence * 100
            elif pipeline == 'rag':
                agent = HDFSRAGBaseline(config=config, model=model)
                response = agent.process(parsed_data)
                hypothesis = response.get('hypothesis', '')
                category = response.get('category', '')
                confidence = response.get('confidence', 0.5) or 0.5
                final_score = confidence * 100
            else:  # multi_agent
                debate_result = self.run_rca_pipeline(parsed_data, config)
                hypothesis = debate_result.get('final_hypothesis', '')
                category = debate_result.get('category', '')
                confidence = debate_result.get('confidence', 0.5)
                final_score = debate_result.get('final_score', 0)
            
            pred_label = self.normalize_prediction(category, hypothesis)
            
            results.append({
                'block_id': block_id,
                'ground_truth': gt_label,
                'predicted_label': pred_label,
                'hypothesis': hypothesis,
                'category': category,
                'confidence': confidence,
                'final_score': final_score,
                'correct': pred_label == gt_label,
                'log_lines': len(parsed_data.get('events', [])),
                'error_count': len(parsed_data.get('error_messages', [])),
            })
            
            status = "✓" if pred_label == gt_label else "✗"
            print(f"  {status} Predicted: {pred_label} (GT: {gt_label})")
        
        return results

    def compute_metrics(
        self,
        rows: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Compute binary classification metrics."""
        labels = ['Normal', 'Anomaly']
        labels_all = labels + ['unknown']
        
        # Build confusion matrix
        confusion: Dict[str, Dict[str, int]] = {gt: {pred: 0 for pred in labels_all} for gt in labels_all}
        for row in rows:
            gt = row.get('ground_truth', 'unknown')
            pred = row.get('predicted_label', 'unknown')
            if gt not in confusion:
                gt = 'unknown'
            if pred not in confusion[gt]:
                pred = 'unknown'
            confusion[gt][pred] += 1
        
        # Calculate per-class metrics
        per_class = {}
        for label in labels:
            tp = confusion.get(label, {}).get(label, 0)
            fp = sum(confusion.get(other, {}).get(label, 0) for other in labels_all if other != label)
            fn = sum(confusion.get(label, {}).get(other, 0) for other in labels_all if other != label)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            support = sum(confusion.get(label, {}).values())
            
            per_class[label] = {
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'support': support,
            }
        
        # Macro averages
        valid_classes = [l for l in labels if per_class[l]['support'] > 0]
        macro_precision = sum(per_class[l]['precision'] for l in valid_classes) / len(valid_classes) if valid_classes else 0
        macro_recall = sum(per_class[l]['recall'] for l in valid_classes) / len(valid_classes) if valid_classes else 0
        macro_f1 = sum(per_class[l]['f1'] for l in valid_classes) / len(valid_classes) if valid_classes else 0
        
        # Accuracy
        correct = sum(1 for row in rows if row.get('predicted_label') == row.get('ground_truth'))
        accuracy = correct / len(rows) if rows else 0
        
        # Unknown predictions
        unknown_count = sum(1 for row in rows if row.get('predicted_label') == 'unknown')
        
        return {
            'labels': labels,
            'accuracy': accuracy,
            'macro_avg': {
                'precision': macro_precision,
                'recall': macro_recall,
                'f1': macro_f1,
            },
            'per_class': per_class,
            'confusion': confusion,
            'total': len(rows),
            'unknown_predictions': unknown_count,
        }


def main():
    parser = argparse.ArgumentParser(description='HDFS_v1 Dataset Validation')
    parser.add_argument('--n-normal', type=int, default=25, help='Number of normal blocks to sample')
    parser.add_argument('--n-anomaly', type=int, default=25, help='Number of anomaly blocks to sample')
    parser.add_argument('--max-lines', type=int, default=500, help='Max log lines per block')
    parser.add_argument('--pipeline', choices=['multi_agent', 'single_agent', 'rag'], default='single_agent')
    parser.add_argument('--model', type=str, default='qwen2:7b', help='LLM model for single_agent/rag')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for sampling')
    parser.add_argument('--output-results', type=str, default='')
    parser.add_argument('--output-metrics', type=str, default='')
    args = parser.parse_args()
    
    validator = HDFSValidator()
    validator.load_labels()
    validator.load_event_traces()
    
    # Select balanced sample
    block_ids = validator.select_balanced_blocks(
        n_normal=args.n_normal,
        n_anomaly=args.n_anomaly,
        seed=args.seed,
    )
    
    # Run validation
    results = validator.validate_blocks(
        block_ids,
        max_lines=args.max_lines,
        pipeline=args.pipeline,
        model=args.model,
    )
    
    # Compute metrics
    metrics = validator.compute_metrics(results)
    
    # Print results
    pipeline_label = {
        'multi_agent': '',
        'single_agent': ' (SINGLE-AGENT)',
        'rag': ' (RAG)'
    }
    
    print("\n" + "=" * 70)
    print(f"HDFS_v1 VALIDATION{pipeline_label.get(args.pipeline, '')}")
    print("=" * 70)
    print(f"Blocks evaluated: {len(results)}")
    print(f"Model: {args.model}")
    
    print("\nBINARY CLASSIFICATION metrics:")
    print(f"  Accuracy: {metrics['accuracy']*100:.1f}%")
    print(f"  Macro P/R/F1: {metrics['macro_avg']['precision']*100:.1f}% / "
          f"{metrics['macro_avg']['recall']*100:.1f}% / {metrics['macro_avg']['f1']*100:.1f}%")
    for cls, stats in metrics['per_class'].items():
        print(f"  {cls}: P={stats['precision']*100:.1f}% R={stats['recall']*100:.1f}% F1={stats['f1']*100:.1f}% (n={stats['support']})")
    
    print(f"\nUnknown predictions: {metrics['unknown_predictions']} ({metrics['unknown_predictions']/len(results)*100:.1f}%)")
    
    # Save results
    results_map = {
        'multi_agent': 'HDFS_MULTI_AGENT_RESULTS.json',
        'single_agent': 'HDFS_SINGLE_AGENT_RESULTS.json',
        'rag': 'HDFS_RAG_RESULTS.json',
    }
    default_results = results_map.get(args.pipeline, 'HDFS_RESULTS.json')
    output_file = Path(args.output_results) if args.output_results.strip() else (Path('docs') / default_results)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open('w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to: {output_file}")
    
    metrics_map = {
        'multi_agent': 'HDFS_MULTI_AGENT_METRICS.json',
        'single_agent': 'HDFS_SINGLE_AGENT_METRICS.json',
        'rag': 'HDFS_RAG_METRICS.json',
    }
    default_metrics = metrics_map.get(args.pipeline, 'HDFS_METRICS.json')
    metrics_file = Path(args.output_metrics) if args.output_metrics.strip() else (Path('docs') / default_metrics)
    with metrics_file.open('w') as f:
        json.dump({
            'metrics': metrics,
            'args': vars(args),
        }, f, indent=2)
    print(f"✓ Metrics saved to: {metrics_file}")
    
    print("\n" + "=" * 70)
    print("✓ VALIDATION COMPLETE!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

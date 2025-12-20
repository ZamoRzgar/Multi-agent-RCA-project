#!/usr/bin/env python3
"""
CMCC/OpenStack Dataset Validation Script

Validates RCA system outputs against CMCC ground truth labels.
Tailored for OpenStack log analysis with appropriate prompts and entity extraction.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import re
import sys
import argparse
from collections import Counter, defaultdict
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

# CMCC failure types (from LogKG dataset)
CMCC_FAILURE_TYPES = {
    'Normal': {
        'description': 'No fault injected - system operating normally',
        'keywords': ['normal', 'healthy', 'no error', 'success'],
        'coarse': 'normal'
    },
    'AMQP': {
        'description': 'Message queue (RabbitMQ/AMQP) connection or communication failure',
        'keywords': ['amqp', 'rabbitmq', 'message queue', 'messaging', 'broker', 'queue connection'],
        'coarse': 'infrastructure'
    },
    'Mysql': {
        'description': 'Database (MySQL) connection or query failure',
        'keywords': ['mysql', 'database', 'db', 'sql', 'mariadb', 'connection refused', 'database error'],
        'coarse': 'infrastructure'
    },
    'Down': {
        'description': 'Service unavailable or not responding',
        'keywords': ['service down', 'unavailable', 'not responding', 'connection refused', 'timeout', 'unreachable'],
        'coarse': 'service_down'
    },
    'CreateErrorFlavor': {
        'description': 'OpenStack flavor creation failed',
        'keywords': ['flavor', 'nova flavor', 'instance type', 'flavor creation', 'compute flavor'],
        'coarse': 'openstack_error'
    },
    'CreateErrorLinuxbridgeAgent': {
        'description': 'Network agent (Linuxbridge) initialization or communication failure',
        'keywords': ['linuxbridge', 'linux bridge', 'network agent', 'neutron agent', 'l2 agent', 'bridge'],
        'coarse': 'openstack_error'
    },
    'CreateErrorNovaConductor': {
        'description': 'Nova conductor service failed during orchestration',
        'keywords': ['nova conductor', 'conductor', 'nova-conductor', 'orchestration', 'compute conductor'],
        'coarse': 'openstack_error'
    }
}

# Coarse category mapping
COARSE_CATEGORIES = {
    'normal': 'normal',
    'infrastructure': 'infrastructure',  # AMQP, Mysql
    'service_down': 'service_down',      # Down
    'openstack_error': 'openstack_error' # CreateError*
}


class CMCCSingleAgentBaseline(BaseAgent):
    """Single-agent baseline with OpenStack-specific prompts."""
    
    def __init__(self, model: str = '', temperature: float = 0.3, max_tokens: int = 1400, **kwargs):
        super().__init__(
            name='CMCCSingleAgent',
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

        return f"""You are an SRE root-cause analyst specializing in OpenStack cloud infrastructure.
Given OpenStack service logs (Nova, Neutron, Keystone, etc.), identify the most likely root cause.

IMPORTANT: You must classify the failure into ONE of these specific categories:
- AMQP: RabbitMQ/message queue connection failures (look for: AMQPConnectionError, reconnect, broker, oslo.messaging)
- Mysql: Database connection or query failures (look for: mysql, database error, connection lost, OperationalError)
- Down: Service unavailable/not responding (look for: connection refused, unreachable, errno 111, timed out)
- CreateErrorFlavor: Nova flavor creation errors (look for: FlavorNotFound, invalid flavor, m1.small failed)
- CreateErrorLinuxbridgeAgent: Neutron Linuxbridge agent errors (look for: linuxbridge, arp_protect, bridge agent failed)
- CreateErrorNovaConductor: Nova conductor service errors (look for: nova-conductor, conductor failed, RPC to conductor)
- Normal: No error detected, system healthy

EXAMPLES:
Example 1 - AMQP failure:
Log: "AMQPConnectionError: [Errno 111] Connection refused... Trying to reconnect to RabbitMQ broker"
Answer: {{"hypothesis": "RabbitMQ message broker connection failure", "category": "AMQP", "confidence": 0.9}}

Example 2 - Mysql failure:
Log: "DBConnectionError: (pymysql.err.OperationalError) Lost connection to MySQL server"
Answer: {{"hypothesis": "MySQL database connection lost", "category": "Mysql", "confidence": 0.9}}

Example 3 - Down failure:
Log: "ConnectionRefusedError: [Errno 111] Connection refused... service not responding"
Answer: {{"hypothesis": "Service is down and not responding to connections", "category": "Down", "confidence": 0.85}}

Example 4 - CreateErrorFlavor:
Log: "FlavorNotFound: Flavor m1.small could not be found... nova.compute.manager failed to create instance"
Answer: {{"hypothesis": "Nova flavor creation failed due to missing flavor definition", "category": "CreateErrorFlavor", "confidence": 0.9}}

Example 5 - CreateErrorLinuxbridgeAgent:
Log: "neutron.plugins.ml2.drivers.linuxbridge.agent failed... arp_protect error... bridge setup failed"
Answer: {{"hypothesis": "Neutron Linuxbridge agent failed during network setup", "category": "CreateErrorLinuxbridgeAgent", "confidence": 0.85}}

Example 6 - CreateErrorNovaConductor:
Log: "nova.conductor.manager RPC timeout... conductor service not responding... failed to schedule instance"
Answer: {{"hypothesis": "Nova conductor service failure preventing instance scheduling", "category": "CreateErrorNovaConductor", "confidence": 0.9}}

Now analyze these logs and return ONLY a JSON object:
{{"hypothesis": "...", "category": "...", "confidence": 0.0-1.0, "suggested_resolution": "..."}}

Known OpenStack components: {entity_text if entity_text else '(none)'}

Top error messages:
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


class CMCCRAGBaseline(BaseAgent):
    """RAG baseline with OpenStack-specific prompts and KG retrieval."""
    
    def __init__(self, config: Dict[str, Any], model: str = '', temperature: float = 0.3, max_tokens: int = 1400, **kwargs):
        super().__init__(
            name='CMCCRAG',
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        if model:
            self.model = model
        self.config = config
        self.kg_agent = KGRetrievalAgent(config=config)

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Retrieve similar incidents from KG
        try:
            kg_data = self.kg_agent.process(input_data)
        except Exception:
            kg_data = {"similar_incidents": [], "entity_contexts": []}
        
        similar_incidents = kg_data.get('similar_incidents', [])
        
        prompt = self._build_prompt(input_data, similar_incidents)
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
            'source': 'rag',
            'similar_incidents_count': len(similar_incidents),
            'raw_response': response,
        }

    def _build_prompt(self, input_data: Dict[str, Any], similar_incidents: List[Dict]) -> str:
        raw_logs = input_data.get('raw_logs', '') or ''
        raw_excerpt = raw_logs[:10000]

        errors = input_data.get('error_messages', []) or []
        error_lines = []
        for e in errors[:30]:
            msg = e.get('message', '') if isinstance(e, dict) else str(e)
            if msg:
                error_lines.append(f"- {msg}")
        error_text = '\n'.join(error_lines) if error_lines else '- (none)'

        # Format similar incidents
        similar_text = ""
        if similar_incidents:
            similar_lines = []
            for i, inc in enumerate(similar_incidents[:5], 1):
                inc_id = inc.get('incident_id', 'unknown')
                root_cause = inc.get('root_cause', 'unknown')
                hypothesis = inc.get('hypothesis', '') or ''
                hypothesis = hypothesis[:200] if hypothesis else ''
                similar_lines.append(f"{i}. [{inc_id}] Root Cause: {root_cause}")
                if hypothesis:
                    similar_lines.append(f"   Hypothesis: {hypothesis}...")
            similar_text = "\n".join(similar_lines)
        else:
            similar_text = "(No similar incidents found)"

        return f"""You are an SRE root-cause analyst specializing in OpenStack cloud infrastructure.
Given OpenStack service logs and similar historical incidents, identify the most likely root cause.

SIMILAR HISTORICAL INCIDENTS FROM KNOWLEDGE BASE:
{similar_text}

IMPORTANT: Classify the failure into ONE of these categories:
- AMQP: RabbitMQ/message queue connection failures (look for: AMQPConnectionError, reconnect, broker, oslo.messaging)
- Mysql: Database connection or query failures (look for: mysql, database error, connection lost, OperationalError)
- Down: Service unavailable/not responding (look for: connection refused, unreachable, errno 111, timed out)
- CreateErrorFlavor: Nova flavor creation errors (look for: FlavorNotFound, invalid flavor, m1.small failed)
- CreateErrorLinuxbridgeAgent: Neutron Linuxbridge agent errors (look for: linuxbridge, arp_protect, bridge agent failed)
- CreateErrorNovaConductor: Nova conductor service errors (look for: nova-conductor, conductor failed, RPC to conductor)
- Normal: No error detected, system healthy

EXAMPLES:
Example 1 - AMQP: {{"hypothesis": "RabbitMQ connection failure", "category": "AMQP", "confidence": 0.9}}
Example 2 - Mysql: {{"hypothesis": "MySQL database connection lost", "category": "Mysql", "confidence": 0.9}}
Example 3 - Down: {{"hypothesis": "Service down and not responding", "category": "Down", "confidence": 0.85}}
Example 4 - CreateErrorFlavor: {{"hypothesis": "Nova flavor creation failed", "category": "CreateErrorFlavor", "confidence": 0.9}}
Example 5 - CreateErrorLinuxbridgeAgent: {{"hypothesis": "Linuxbridge agent failed", "category": "CreateErrorLinuxbridgeAgent", "confidence": 0.85}}
Example 6 - CreateErrorNovaConductor: {{"hypothesis": "Nova conductor service failure", "category": "CreateErrorNovaConductor", "confidence": 0.9}}

Return ONLY a JSON object:
{{"hypothesis": "...", "category": "...", "confidence": 0.0-1.0, "suggested_resolution": "..."}}

Top error messages:
{error_text}

Log excerpt:
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
        return {}


class CMCCValidator:
    """Validator for CMCC/OpenStack dataset."""
    
    def __init__(self):
        self.results = []
        self._labels_by_case_id = {}

    def load_config(self) -> Dict[str, Any]:
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        kg_config = config.get('knowledge_graph', {})
        if kg_config.get('password') == '${NEO4J_PASSWORD}':
            kg_config['password'] = '1997Amaterasu'
        
        return config

    def load_labels(self) -> Dict[str, str]:
        """Load CMCC labels from config.json."""
        config_file = Path(__file__).parent.parent / "loghub" / "LogKG" / "data" / "config.json"
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        for label, case_ids in config.items():
            for case_id in case_ids:
                self._labels_by_case_id[case_id] = label
        
        return self._labels_by_case_id

    def load_case_logs(self, case_id: str, max_lines: int = 2500) -> str:
        """Load logs from CMCC case CSV file."""
        case_file = Path(__file__).parent.parent / "loghub" / "LogKG" / "data" / "CMCC_case" / f"{case_id}.csv"
        if not case_file.exists():
            raise FileNotFoundError(f"Case file not found: {case_file}")
        
        df = pd.read_csv(case_file)
        
        # Filter for important log levels
        keep_levels = {'ERROR', 'WARN', 'WARNING', 'CRITICAL', 'FATAL', 'INFO'}
        if 'Level' in df.columns:
            # Prioritize error/warning logs
            error_df = df[df['Level'].str.upper().isin({'ERROR', 'WARN', 'WARNING', 'CRITICAL', 'FATAL'})]
        else:
            error_df = pd.DataFrame()
        
        selected: List[str] = []
        
        # Add header lines for context
        for _, row in df.head(100).iterrows():
            timestamp = f"{row.get('Date', '')} {row.get('Time', '')}"
            level = row.get('Level', 'INFO')
            component = row.get('Component', '')
            content = row.get('Content', '')
            line = f"{timestamp} {level} [{component}] {content}"
            selected.append(line)
        
        # Add error/warning lines
        for _, row in error_df.iterrows():
            timestamp = f"{row.get('Date', '')} {row.get('Time', '')}"
            level = row.get('Level', 'INFO')
            component = row.get('Component', '')
            content = row.get('Content', '')
            line = f"{timestamp} {level} [{component}] {content}"
            if line not in selected:
                selected.append(line)
                if len(selected) >= max_lines:
                    break
        
        return '\n'.join(selected[:max_lines])

    def build_parsed_data(self, raw_logs: str) -> Dict[str, Any]:
        """Build parsed data structure from raw logs."""
        events = []
        entities = []
        error_messages = []
        
        component_seen = set()
        
        for raw_line in raw_logs.splitlines():
            # Parse OpenStack log format
            # Format: YYYY-MM-DD HH:MM:SS.mmm LEVEL [Component] Content
            m = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\S*\s+(\w+)\s+\[([^\]]*)\]\s*(.*)$", raw_line)
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
            
            # Extract components as entities
            if component and component not in component_seen:
                component_seen.add(component)
                entities.append({
                    "type": "openstack_component",
                    "value": component,
                    "component": component,
                })
            
            # Collect error messages
            if level.upper() in ('ERROR', 'WARN', 'WARNING', 'CRITICAL', 'FATAL'):
                error_messages.append({
                    "level": level,
                    "component": component,
                    "message": message,
                })
        
        return {
            "raw_logs": raw_logs,
            "events": events,
            "entities": entities,
            "error_messages": error_messages,
            "timeline": events,
        }

    def normalize_prediction(self, category: str, hypothesis: str) -> str:
        """Normalize LLM prediction to CMCC label."""
        text = f"{category or ''} {hypothesis or ''}".lower()
        
        # Direct category match
        category_clean = (category or '').strip()
        if category_clean in CMCC_FAILURE_TYPES:
            return category_clean
        
        # Score-based matching - count keyword hits for each category
        scores = {
            'AMQP': 0,
            'Mysql': 0,
            'Down': 0,
            'CreateErrorFlavor': 0,
            'CreateErrorLinuxbridgeAgent': 0,
            'CreateErrorNovaConductor': 0,
            'Normal': 0,
        }
        
        # AMQP keywords (RabbitMQ/messaging issues)
        amqp_keywords = ['amqp', 'rabbitmq', 'message queue', 'messaging', 'broker', 
                         'amqpconnectionerror', 'connection to amqp', 'reconnect', 
                         'rpc timeout', 'rpc_response_timeout', 'oslo.messaging']
        for kw in amqp_keywords:
            if kw in text:
                scores['AMQP'] += 2 if kw in ['amqp', 'rabbitmq', 'amqpconnectionerror'] else 1
        
        # MySQL keywords (database issues)
        mysql_keywords = ['mysql', 'database', 'mariadb', 'sql error', 'db connection',
                          'dbconnectionerror', 'operationalerror', 'database connection',
                          'lost connection', 'mysql server', 'query failed']
        for kw in mysql_keywords:
            if kw in text:
                scores['Mysql'] += 2 if kw in ['mysql', 'mariadb', 'dbconnectionerror'] else 1
        
        # Down keywords (service unavailable)
        down_keywords = ['service down', 'unavailable', 'not responding', 'connection refused',
                         'service unavailable', 'failed to connect', 'unreachable', 
                         'network is unreachable', 'errno 101', 'errno 111', 'timed out']
        for kw in down_keywords:
            if kw in text:
                scores['Down'] += 2 if kw in ['service down', 'connection refused'] else 1
        
        # CreateErrorFlavor keywords
        flavor_keywords = ['flavor', 'nova flavor', 'instance type', 'flavornotfound',
                           'flavor creation', 'invalid flavor', 'm1.small', 'm1.medium']
        for kw in flavor_keywords:
            if kw in text:
                scores['CreateErrorFlavor'] += 2 if 'flavor' in kw else 1
        
        # CreateErrorLinuxbridgeAgent keywords
        linuxbridge_keywords = ['linuxbridge', 'linux bridge', 'l2 agent', 'neutron agent',
                                'linuxbridge_neutron_agent', 'bridge agent', 'arp_protect',
                                'linuxbridgeagent', 'br-int', 'br-ex']
        for kw in linuxbridge_keywords:
            if kw in text:
                scores['CreateErrorLinuxbridgeAgent'] += 2 if 'linuxbridge' in kw else 1
        
        # CreateErrorNovaConductor keywords  
        conductor_keywords = ['nova conductor', 'conductor', 'nova-conductor', 'conductor service',
                              'conductor error', 'nova.conductor', 'conductor failed']
        for kw in conductor_keywords:
            if kw in text:
                scores['CreateErrorNovaConductor'] += 2 if 'conductor' in kw else 1
        
        # Normal keywords (healthy system)
        normal_keywords = ['normal operation', 'healthy', 'no error', 'no issue', 'working correctly',
                           'functioning normally', 'typical operations', 'routine', 'expected behavior']
        for kw in normal_keywords:
            if kw in text:
                scores['Normal'] += 1
        
        # Return highest scoring category if score > 0
        max_score = max(scores.values())
        if max_score > 0:
            for label, score in scores.items():
                if score == max_score:
                    return label
        
        return 'unknown'

    def get_coarse_label(self, label: str) -> str:
        """Get coarse category for a label."""
        if label in CMCC_FAILURE_TYPES:
            return CMCC_FAILURE_TYPES[label]['coarse']
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

    def validate_cases(
        self,
        case_ids: List[str],
        max_lines: int = 2500,
        pipeline: str = 'multi_agent',
        model: str = '',
    ) -> List[Dict[str, Any]]:
        """Validate CMCC cases against ground truth."""
        config = self.load_config()
        results = []
        
        for idx, case_id in enumerate(case_ids, 1):
            gt_label = self._labels_by_case_id.get(case_id, 'unknown')
            gt_coarse = self.get_coarse_label(gt_label)
            
            print(f"[{idx}/{len(case_ids)}] Processing {case_id} (GT: {gt_label})...")
            
            try:
                raw_logs = self.load_case_logs(case_id, max_lines=max_lines)
            except FileNotFoundError as e:
                print(f"  ⚠ Skipping: {e}")
                continue
            
            parsed_data = self.build_parsed_data(raw_logs)
            
            if pipeline == 'single_agent':
                agent = CMCCSingleAgentBaseline(model=model)
                response = agent.process(parsed_data)
                hypothesis = response.get('hypothesis', '')
                category = response.get('category', '')
                confidence = response.get('confidence', 0.5) or 0.5
                final_score = confidence * 100
            elif pipeline == 'rag':
                agent = CMCCRAGBaseline(config=config, model=model)
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
            pred_coarse = self.get_coarse_label(pred_label)
            
            results.append({
                'case_id': case_id,
                'ground_truth': gt_label,
                'ground_truth_coarse': gt_coarse,
                'predicted_failure_type': pred_label,
                'predicted_failure_type_coarse': pred_coarse,
                'hypothesis': hypothesis,
                'category': category,
                'confidence': confidence,
                'final_score': final_score,
                'correct_strict': pred_label == gt_label,
                'correct_coarse': pred_coarse == gt_coarse,
            })
            
            status = "✓" if pred_label == gt_label else "✗"
            print(f"  {status} Predicted: {pred_label} (GT: {gt_label})")
        
        return results

    def compute_metrics(
        self,
        rows: List[Dict[str, Any]],
        labels: List[str],
        pred_key: str = 'predicted_failure_type',
        gt_key: str = 'ground_truth',
    ) -> Dict[str, Any]:
        """Compute classification metrics."""
        labels_all = list(labels)
        if 'unknown' not in labels_all:
            labels_all.append('unknown')
        
        # Build confusion matrix
        confusion: Dict[str, Dict[str, int]] = {gt: {pred: 0 for pred in labels_all} for gt in labels_all}
        for row in rows:
            gt = row.get(gt_key, 'unknown')
            pred = row.get(pred_key, 'unknown')
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
        correct = sum(1 for row in rows if row.get(pred_key) == row.get(gt_key))
        accuracy = correct / len(rows) if rows else 0
        
        return {
            'labels': labels,
            'labels_all': labels_all,
            'accuracy': accuracy,
            'macro_avg': {
                'precision': macro_precision,
                'recall': macro_recall,
                'f1': macro_f1,
            },
            'per_class': per_class,
            'confusion': confusion,
            'total': len(rows),
            'unknown_predictions': sum(1 for row in rows if row.get(pred_key) == 'unknown'),
        }


def main():
    parser = argparse.ArgumentParser(description='CMCC/OpenStack Dataset Validation')
    parser.add_argument('--max-cases', type=int, default=3, help='Max cases to process')
    parser.add_argument('--all', action='store_true', help='Process all 93 cases')
    parser.add_argument('--cases', type=str, default='', help='Comma-separated case IDs')
    parser.add_argument('--max-lines', type=int, default=2500, help='Max log lines per case')
    parser.add_argument('--pipeline', choices=['multi_agent', 'single_agent', 'rag'], default='single_agent')
    parser.add_argument('--model', type=str, default='qwen2:7b', help='LLM model for single_agent/rag')
    parser.add_argument('--output-results', type=str, default='')
    parser.add_argument('--output-metrics', type=str, default='')
    args = parser.parse_args()
    
    validator = CMCCValidator()
    labels = validator.load_labels()
    
    # Select cases
    if args.cases.strip():
        case_ids = [c.strip() for c in args.cases.split(',') if c.strip()]
    elif args.all:
        case_ids = sorted(labels.keys())
    else:
        case_ids = sorted(labels.keys())[:max(1, args.max_cases)]
    
    # Run validation
    results = validator.validate_cases(
        case_ids,
        max_lines=args.max_lines,
        pipeline=args.pipeline,
        model=args.model,
    )
    
    # Compute metrics
    strict_labels = ['Normal', 'AMQP', 'Mysql', 'Down', 'CreateErrorFlavor', 'CreateErrorLinuxbridgeAgent', 'CreateErrorNovaConductor']
    strict_metrics = validator.compute_metrics(
        results,
        labels=strict_labels,
        pred_key='predicted_failure_type',
        gt_key='ground_truth',
    )
    
    coarse_labels = ['normal', 'infrastructure', 'service_down', 'openstack_error']
    coarse_metrics = validator.compute_metrics(
        results,
        labels=coarse_labels,
        pred_key='predicted_failure_type_coarse',
        gt_key='ground_truth_coarse',
    )
    
    # Print results
    pipeline_label = {
        'multi_agent': '',
        'single_agent': ' (SINGLE-AGENT)',
        'rag': ' (RAG)'
    }
    
    print("\n" + "=" * 70)
    print(f"CMCC VALIDATION{pipeline_label.get(args.pipeline, '')}")
    print("=" * 70)
    print(f"Cases evaluated: {len(results)}")
    print(f"Model: {args.model}")
    
    print("\nSTRICT (7-class) metrics:")
    print(f"  Accuracy: {strict_metrics['accuracy']*100:.1f}%")
    print(f"  Macro P/R/F1: {strict_metrics['macro_avg']['precision']*100:.1f}% / "
          f"{strict_metrics['macro_avg']['recall']*100:.1f}% / {strict_metrics['macro_avg']['f1']*100:.1f}%")
    for cls, stats in strict_metrics['per_class'].items():
        print(f"  {cls}: P={stats['precision']*100:.1f}% R={stats['recall']*100:.1f}% F1={stats['f1']*100:.1f}% (n={stats['support']})")
    
    print("\nCOARSE (4-class) metrics:")
    print(f"  Accuracy: {coarse_metrics['accuracy']*100:.1f}%")
    print(f"  Macro P/R/F1: {coarse_metrics['macro_avg']['precision']*100:.1f}% / "
          f"{coarse_metrics['macro_avg']['recall']*100:.1f}% / {coarse_metrics['macro_avg']['f1']*100:.1f}%")
    for cls, stats in coarse_metrics['per_class'].items():
        print(f"  {cls}: P={stats['precision']*100:.1f}% R={stats['recall']*100:.1f}% F1={stats['f1']*100:.1f}% (n={stats['support']})")
    
    # Save results
    results_map = {
        'multi_agent': 'CMCC_MULTI_AGENT_RESULTS.json',
        'single_agent': 'CMCC_SINGLE_AGENT_RESULTS.json',
        'rag': 'CMCC_RAG_RESULTS.json',
    }
    default_results = results_map.get(args.pipeline, 'CMCC_RESULTS.json')
    output_file = Path(args.output_results) if args.output_results.strip() else (Path('docs') / default_results)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open('w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to: {output_file}")
    
    metrics_map = {
        'multi_agent': 'CMCC_MULTI_AGENT_METRICS.json',
        'single_agent': 'CMCC_SINGLE_AGENT_METRICS.json',
        'rag': 'CMCC_RAG_METRICS.json',
    }
    default_metrics = metrics_map.get(args.pipeline, 'CMCC_METRICS.json')
    metrics_file = Path(args.output_metrics) if args.output_metrics.strip() else (Path('docs') / default_metrics)
    with metrics_file.open('w') as f:
        json.dump({
            'strict': strict_metrics,
            'coarse': coarse_metrics,
            'args': vars(args),
        }, f, indent=2)
    print(f"✓ Metrics saved to: {metrics_file}")
    
    print("\n" + "=" * 70)
    print("✓ VALIDATION COMPLETE!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

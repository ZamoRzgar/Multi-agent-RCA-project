"""
Loghub Dataset Loader.

This module provides utilities to load and process loghub datasets
for RCA testing.
"""

import pandas as pd
from typing import Dict, Any, List, Tuple
from pathlib import Path
from loguru import logger
import re


class LoghubLoader:
    """
    Loader for loghub datasets.
    
    Handles loading structured CSV files, templates, and creating
    incident scenarios for RCA testing.
    """
    
    def __init__(self, loghub_root: str = "loghub"):
        """
        Initialize loghub loader.
        
        Args:
            loghub_root: Root directory of loghub datasets
        """
        self.loghub_root = Path(loghub_root)
        logger.info(f"Initialized LoghubLoader with root: {self.loghub_root}")
    
    def load_dataset(
        self,
        dataset_name: str,
        sample_size: int = None
    ) -> Dict[str, Any]:
        """
        Load a loghub dataset.
        
        Args:
            dataset_name: Name of dataset (e.g., 'HDFS', 'Hadoop', 'Spark')
            sample_size: Number of log lines to sample (None = all)
            
        Returns:
            Dictionary with:
                - logs: DataFrame of structured logs
                - templates: DataFrame of log templates
                - dataset_name: Name of the dataset
                - num_logs: Number of log entries
        """
        dataset_path = self.loghub_root / dataset_name
        
        if not dataset_path.exists():
            raise ValueError(f"Dataset not found: {dataset_path}")
        
        logger.info(f"Loading dataset: {dataset_name}")
        
        # Load structured logs
        structured_file = dataset_path / f"{dataset_name}_2k.log_structured.csv"
        if not structured_file.exists():
            raise ValueError(f"Structured file not found: {structured_file}")
        
        logs_df = pd.read_csv(structured_file)
        
        if sample_size:
            logs_df = logs_df.head(sample_size)
        
        logger.info(f"Loaded {len(logs_df)} log entries")
        
        # Load templates
        templates_file = dataset_path / f"{dataset_name}_2k.log_templates.csv"
        templates_df = None
        if templates_file.exists():
            templates_df = pd.read_csv(templates_file)
            logger.info(f"Loaded {len(templates_df)} log templates")
        
        return {
            "logs": logs_df,
            "templates": templates_df,
            "dataset_name": dataset_name,
            "num_logs": len(logs_df),
            "path": str(dataset_path)
        }
    
    def create_incident_from_logs(
        self,
        logs_df: pd.DataFrame,
        start_idx: int,
        end_idx: int,
        incident_type: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Create an incident scenario from a log slice.
        
        Args:
            logs_df: DataFrame of logs
            start_idx: Start index of incident
            end_idx: End index of incident
            incident_type: Type of incident (for ground truth)
            
        Returns:
            Incident data in system format
        """
        incident_logs = logs_df.iloc[start_idx:end_idx]
        
        # Extract raw log messages
        raw_logs = []
        for _, row in incident_logs.iterrows():
            timestamp = f"{row.get('Date', '')} {row.get('Time', '')}"
            level = row.get('Level', 'INFO')
            component = row.get('Component', '')
            content = row.get('Content', '')
            
            log_line = f"{timestamp} {level} {component}: {content}"
            raw_logs.append(log_line)
        
        # Parse into events
        events = []
        for _, row in incident_logs.iterrows():
            event = {
                "timestamp": f"{row.get('Date', '')} {row.get('Time', '')}",
                "level": row.get('Level', 'INFO'),
                "component": row.get('Component', ''),
                "message": row.get('Content', ''),
                "event_id": row.get('EventId', ''),
                "template": row.get('EventTemplate', '')
            }
            events.append(event)
        
        # Extract entities (IPs, blocks, etc.)
        entities = self._extract_entities(incident_logs)
        
        # Extract error messages
        error_messages = self._extract_errors(incident_logs)
        
        logger.info(f"Created incident with {len(events)} events, "
                   f"{len(entities)} entities, {len(error_messages)} errors")
        
        return {
            "raw_logs": "\n".join(raw_logs),
            "events": events,
            "entities": entities,
            "error_messages": error_messages,
            "incident_type": incident_type,
            "num_events": len(events)
        }
    
    def _extract_entities(self, logs_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract entities from logs (IPs, blocks, components)."""
        entities = []
        seen = set()
        
        for _, row in logs_df.iterrows():
            content = str(row.get('Content', ''))
            
            # Extract IP addresses
            ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', content)
            for ip in ips:
                if ip not in seen:
                    entities.append({
                        "type": "ip_address",
                        "value": ip,
                        "component": row.get('Component', '')
                    })
                    seen.add(ip)
            
            # Extract block IDs
            blocks = re.findall(r'blk_-?\d+', content)
            for block in blocks:
                if block not in seen:
                    entities.append({
                        "type": "block_id",
                        "value": block,
                        "component": row.get('Component', '')
                    })
                    seen.add(block)
            
            # Extract components
            component = row.get('Component', '')
            if component and component not in seen:
                entities.append({
                    "type": "component",
                    "value": component,
                    "component": component
                })
                seen.add(component)
        
        return entities
    
    def _extract_errors(self, logs_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract error messages from logs."""
        errors = []
        
        for _, row in logs_df.iterrows():
            level = row.get('Level', '')
            content = str(row.get('Content', ''))
            
            # Check for error level or error keywords
            if level in ['ERROR', 'FATAL', 'WARN'] or \
               any(keyword in content.lower() for keyword in 
                   ['error', 'exception', 'failed', 'failure', 'fatal']):
                
                errors.append({
                    "timestamp": f"{row.get('Date', '')} {row.get('Time', '')}",
                    "level": level,
                    "component": row.get('Component', ''),
                    "message": content,
                    "event_id": row.get('EventId', '')
                })
        
        return errors
    
    def create_incident_scenarios(
        self,
        dataset_name: str,
        num_scenarios: int = 5,
        logs_per_scenario: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Create multiple incident scenarios from a dataset.
        
        Args:
            dataset_name: Name of dataset
            num_scenarios: Number of scenarios to create
            logs_per_scenario: Number of log lines per scenario
            
        Returns:
            List of incident scenarios
        """
        dataset = self.load_dataset(dataset_name)
        logs_df = dataset["logs"]
        
        scenarios = []
        total_logs = len(logs_df)
        
        # Create evenly spaced scenarios
        step = max(1, (total_logs - logs_per_scenario) // num_scenarios)
        
        for i in range(num_scenarios):
            start_idx = i * step
            end_idx = min(start_idx + logs_per_scenario, total_logs)
            
            if end_idx - start_idx < 10:  # Skip if too few logs
                continue
            
            incident = self.create_incident_from_logs(
                logs_df,
                start_idx,
                end_idx,
                incident_type=f"{dataset_name}_incident_{i+1}"
            )
            
            incident["scenario_id"] = i + 1
            incident["dataset"] = dataset_name
            scenarios.append(incident)
        
        logger.info(f"Created {len(scenarios)} incident scenarios from {dataset_name}")
        
        return scenarios
    
    def get_failure_types(self, dataset_name: str) -> List[str]:
        """
        Get known failure types for a dataset.
        
        Args:
            dataset_name: Name of dataset
            
        Returns:
            List of failure types
        """
        failure_types = {
            "HDFS": [
                "disk_full",
                "block_corruption",
                "datanode_failure",
                "replication_failure",
                "network_issue"
            ],
            "Hadoop": [
                "machine_down",
                "network_disconnection",
                "disk_full",
                "task_failure",
                "resource_exhaustion"
            ],
            "Spark": [
                "executor_failure",
                "memory_exhaustion",
                "shuffle_failure",
                "task_timeout",
                "driver_failure"
            ],
            "OpenStack": [
                "service_failure",
                "api_timeout",
                "database_connection",
                "authentication_failure",
                "resource_quota"
            ],
            "Zookeeper": [
                "leader_election_failure",
                "network_partition",
                "session_timeout",
                "connection_loss",
                "quorum_loss"
            ]
        }
        
        return failure_types.get(dataset_name, ["unknown"])


def load_loghub_dataset(
    dataset_name: str,
    sample_size: int = None
) -> Dict[str, Any]:
    """
    Convenience function to load a loghub dataset.
    
    Args:
        dataset_name: Name of dataset (e.g., 'HDFS', 'Hadoop')
        sample_size: Number of logs to sample
        
    Returns:
        Dataset dictionary
    """
    loader = LoghubLoader()
    return loader.load_dataset(dataset_name, sample_size)


def create_test_scenarios(
    dataset_name: str,
    num_scenarios: int = 5
) -> List[Dict[str, Any]]:
    """
    Convenience function to create test scenarios.
    
    Args:
        dataset_name: Name of dataset
        num_scenarios: Number of scenarios to create
        
    Returns:
        List of incident scenarios
    """
    loader = LoghubLoader()
    return loader.create_incident_scenarios(dataset_name, num_scenarios)


if __name__ == "__main__":
    # Test the loader
    print("Testing LoghubLoader...")
    
    # Load HDFS dataset
    loader = LoghubLoader()
    dataset = loader.load_dataset("HDFS", sample_size=100)
    
    print(f"\nDataset: {dataset['dataset_name']}")
    print(f"Logs: {dataset['num_logs']}")
    print(f"Templates: {len(dataset['templates']) if dataset['templates'] is not None else 0}")
    
    # Create a sample incident
    incident = loader.create_incident_from_logs(
        dataset["logs"],
        0,
        50,
        "disk_full"
    )
    
    print(f"\nIncident:")
    print(f"Events: {incident['num_events']}")
    print(f"Entities: {len(incident['entities'])}")
    print(f"Errors: {len(incident['error_messages'])}")
    
    # Create scenarios
    scenarios = loader.create_incident_scenarios("HDFS", num_scenarios=3, logs_per_scenario=50)
    print(f"\nCreated {len(scenarios)} scenarios")

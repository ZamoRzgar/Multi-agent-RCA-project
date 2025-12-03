"""
Main entry point for Multi-Agent RCA System.
"""

import argparse
import yaml
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

from src.agents import LogParserAgent, KGRetrievalAgent, RCAReasonerAgent, JudgeAgent
from src.debate import DebateProtocol


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def setup_logging(config: dict):
    """Setup logging configuration."""
    log_config = config.get('logging', {})
    log_level = log_config.get('level', 'INFO')
    log_file = log_config.get('file', 'logs/aetherlog.log')
    
    # Remove default handler
    logger.remove()
    
    # Add file handler
    logger.add(
        log_file,
        level=log_level,
        format=log_config.get('format', '{time} - {name} - {level} - {message}'),
        rotation="10 MB"
    )
    
    # Add console handler if enabled
    if log_config.get('console', True):
        logger.add(
            lambda msg: print(msg, end=''),
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
        )


def initialize_agents(config: dict):
    """Initialize all agents."""
    agent_config = config.get('agents', {})
    llm_config = config.get('llm', {})
    
    # Log Parser Agent
    log_parser = LogParserAgent(
        model=llm_config.get('model'),
        temperature=agent_config.get('log_parser', {}).get('temperature', 0.3),
        config=config.get('log_parsing', {})
    )
    
    # KG Retrieval Agent
    kg_retrieval = KGRetrievalAgent(
        model=llm_config.get('model'),
        config=agent_config.get('kg_retrieval', {})
    )
    
    # RCA Reasoner Agents
    reasoner_config = agent_config.get('rca_reasoners', {})
    reasoner_types = reasoner_config.get('types', ['log_focused', 'kg_focused', 'hybrid'])
    
    reasoners = []
    for rtype in reasoner_types:
        focus = rtype.replace('_focused', '').replace('_', '')
        reasoner = RCAReasonerAgent(
            focus=focus,
            model=llm_config.get('model'),
            temperature=reasoner_config.get('temperature', 0.7)
        )
        reasoners.append(reasoner)
    
    # Judge Agent
    judge = JudgeAgent(
        model=llm_config.get('model'),
        temperature=agent_config.get('judge', {}).get('temperature', 0.2),
        config=agent_config.get('judge', {})
    )
    
    return log_parser, kg_retrieval, reasoners, judge


def run_rca(log_file: str, config: dict):
    """
    Run RCA on a log file.
    
    Args:
        log_file: Path to log file
        config: Configuration dictionary
    """
    logger.info(f"Starting RCA for {log_file}")
    
    # Initialize agents
    log_parser, kg_retrieval, reasoners, judge = initialize_agents(config)
    
    # Initialize debate protocol
    debate_config = config.get('debate', {})
    debate = DebateProtocol(
        reasoners=reasoners,
        judge=judge,
        max_rounds=debate_config.get('max_rounds', 2),
        consensus_threshold=debate_config.get('consensus_threshold', 0.8)
    )
    
    # Load log file
    with open(log_file, 'r') as f:
        raw_logs = f.read()
    
    # Step 1: Parse logs
    logger.info("Step 1: Parsing logs")
    parsed_logs = log_parser.process({"raw_logs": raw_logs})
    
    # Step 2: Retrieve KG facts
    logger.info("Step 2: Retrieving KG facts")
    kg_facts = kg_retrieval.process(parsed_logs)
    
    # Step 3: Run debate
    logger.info("Step 3: Running multi-agent debate")
    result = debate.run(parsed_logs, kg_facts)
    
    # Display results
    logger.info("=" * 80)
    logger.info("RCA RESULTS")
    logger.info("=" * 80)
    logger.info(f"Root Cause: {result['root_cause']}")
    logger.info(f"Explanation: {result['explanation']}")
    logger.info(f"Confidence: {result['confidence']:.2f}")
    logger.info("=" * 80)
    
    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AetherLog 2.0 Multi-Agent RCA System"
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        required=True,
        help='Path to log file for RCA'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Path to save results (optional)'
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    setup_logging(config)
    
    logger.info("AetherLog 2.0 Multi-Agent RCA System")
    logger.info(f"Configuration: {args.config}")
    
    # Run RCA
    result = run_rca(args.log_file, config)
    
    # Save results if output path specified
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()

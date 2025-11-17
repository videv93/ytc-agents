#!/usr/bin/env python3
"""
Visualize the YTC Trading System LangGraph Workflow

This script creates visual representations of the trading workflow graph
for easier understanding of agent relationships and execution flow.

Usage:
    python3 examples/visualize_workflow.py
    python3 examples/visualize_workflow.py --output graphs/workflow.png
    python3 examples/visualize_workflow.py --langsmith  # Enable LangSmith tracing
"""

import os
import sys
import argparse
from dotenv import load_dotenv
import yaml
import structlog

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import MasterOrchestrator

logger = structlog.get_logger()


def load_configuration() -> dict:
    """Load configuration from YAML files and environment"""
    config = {
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'model': os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514'),
        'max_tokens': 4096,
        'hummingbot_gateway_url': os.getenv('HUMMINGBOT_GATEWAY_URL', 'http://localhost:8000'),
        'hummingbot_username': os.getenv('HUMMINGBOT_USERNAME'),
        'hummingbot_password': os.getenv('HUMMINGBOT_PASSWORD'),
        'connector': os.getenv('CONNECTOR', 'binance_perpetual_testnet'),
        'account_config': {
            'initial_balance': float(os.getenv('INITIAL_BALANCE', '100000.0'))
        }
    }

    # Load session configuration
    session_config_path = 'config/session_config.yaml'
    if os.path.exists(session_config_path):
        with open(session_config_path, 'r') as f:
            config['session_config'] = yaml.safe_load(f)
    else:
        config['session_config'] = {
            'market': os.getenv('TRADING_MARKET', 'crypto'),
            'instrument': os.getenv('TRADING_INSTRUMENT', 'ETH-USDT'),
            'session_start_time': os.getenv('SESSION_START_TIME', '09:30:00'),
            'duration_hours': int(os.getenv('SESSION_DURATION_HOURS', '3'))
        }

    # Load risk configuration
    risk_config_path = 'config/risk_config.yaml'
    if os.path.exists(risk_config_path):
        with open(risk_config_path, 'r') as f:
            config['risk_config'] = yaml.safe_load(f)
    else:
        config['risk_config'] = {
            'risk_per_trade_pct': float(os.getenv('RISK_PER_TRADE_PCT', '1.0')),
            'max_session_risk_pct': float(os.getenv('MAX_SESSION_RISK_PCT', '3.0')),
            'max_positions': int(os.getenv('MAX_POSITIONS', '3')),
            'max_total_exposure_pct': float(os.getenv('MAX_TOTAL_EXPOSURE_PCT', '3.0')),
            'consecutive_loss_limit': int(os.getenv('CONSECUTIVE_LOSS_LIMIT', '5'))
        }

    return config


def main():
    """Main visualization function"""
    parser = argparse.ArgumentParser(
        description='Visualize the YTC Trading System LangGraph workflow'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path for visualization (PNG/SVG)',
        default=None
    )
    parser.add_argument(
        '--langsmith',
        action='store_true',
        help='Enable LangSmith tracing for this visualization'
    )
    parser.add_argument(
        '--ascii',
        action='store_true',
        help='Output ASCII representation instead of PNG'
    )

    args = parser.parse_args()

    # Load environment
    load_dotenv()

    # Enable LangSmith if requested
    if args.langsmith:
        if not os.getenv('LANGSMITH_API_KEY'):
            print("Error: LANGSMITH_API_KEY not set in .env file")
            print("Get one from https://smith.langchain.com")
            sys.exit(1)
        os.environ['LANGCHAIN_TRACING_V2'] = 'true'
        print("✓ LangSmith tracing enabled")

    # Load configuration
    print("Loading configuration...")
    config = load_configuration()

    # Initialize orchestrator
    print("Initializing orchestrator...")
    orchestrator = MasterOrchestrator(config)

    # Generate visualization
    print("\nGenerating workflow visualization...")
    
    if args.ascii:
        # ASCII visualization
        visualization = orchestrator.visualize_graph()
        print("\n" + "="*70)
        print("WORKFLOW GRAPH (ASCII)")
        print("="*70)
        print(visualization)
    else:
        # PNG visualization
        output_path = args.output or 'graphs/workflow.png'
        
        # Create graphs directory if needed
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        result = orchestrator.visualize_graph(output_path=output_path)
        print(f"✓ Visualization saved to: {result}")
        
        # If LangSmith is enabled, print the URL
        if args.langsmith and os.getenv('LANGSMITH_PROJECT'):
            project = os.getenv('LANGSMITH_PROJECT')
            print(f"\n✓ View runs in LangSmith: https://smith.langchain.com/projects/{project}")

    print("\nWorkflow visualization complete!")
    print("\nAgent phases:")
    print("  Pre-Market:     system_init → risk_mgmt → market_structure → economic_calendar")
    print("  Session Open:   trend_definition → strength_weakness")
    print("  Active Trading: setup_scanner → entry_execution → trade_management → exit_execution")
    print("  Post-Market:    session_review → performance_analytics → learning_optimization → next_session_prep")
    print("  Continuous:     monitoring, contingency, logging_audit (run during all phases)")


if __name__ == '__main__':
    main()

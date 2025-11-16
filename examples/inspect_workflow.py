#!/usr/bin/env python
"""
Inspect Workflow Structure
Shows the LangGraph workflow structure and connections
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import MasterOrchestrator


def main():
    """Display workflow structure"""

    print("=" * 70)
    print("YTC Trading System - Workflow Structure")
    print("=" * 70)
    print()

    # Create minimal config
    config = {
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY', 'test-key'),
        'session_config': {'market': 'forex', 'instrument': 'GBP/USD'},
        'risk_config': {'risk_per_trade_pct': 1.0, 'max_session_risk_pct': 3.0},
        'account_config': {'initial_balance': 100000.0}
    }

    # Initialize orchestrator
    print("🔧 Initializing orchestrator...")
    orchestrator = MasterOrchestrator(config)
    print()

    # List all agents
    print("📋 Registered Agents:")
    print()
    for i, (agent_id, agent) in enumerate(orchestrator.agents.items(), 1):
        agent_class = agent.__class__.__name__
        print(f"  {i:2d}. {agent_id:25s} - {agent_class}")
    print()

    # Show workflow phases
    print("=" * 70)
    print("Workflow Phases")
    print("=" * 70)
    print()

    phases = {
        'PRE-MARKET': [
            'system_init',
            'risk_mgmt',
            'market_structure',
            'economic_calendar',
            'contingency',
            'emergency_check'
        ],
        'SESSION OPEN': [
            'trend_definition',
            'strength_weakness'
        ],
        'ACTIVE TRADING': [
            'monitoring',
            'setup_scanner',
            'entry_execution',
            'trade_management',
            'exit_execution'
        ],
        'POST-MARKET': [
            'session_review',
            'performance_analytics',
            'learning_optimization',
            'next_session_prep'
        ],
        'CONTINUOUS': [
            'logging_audit',
            'contingency',
            'monitoring'
        ]
    }

    for phase, agents in phases.items():
        print(f"{phase}:")
        for agent in agents:
            if agent in orchestrator.agents:
                print(f"  ✅ {agent}")
            else:
                print(f"  ⚠️  {agent} (control node)")
        print()

    # Show initial state structure
    print("=" * 70)
    print("Initial Trading State Structure")
    print("=" * 70)
    print()

    state = orchestrator.session_state
    print("State Fields:")
    for key in sorted(state.keys()):
        value = state[key]
        value_type = type(value).__name__
        if isinstance(value, (dict, list)) and len(str(value)) > 50:
            display_value = f"{value_type} (length: {len(value)})"
        else:
            display_value = f"{value_type}: {value}"
        print(f"  {key:25s} = {display_value}")
    print()

    # Show routing logic
    print("=" * 70)
    print("Phase Routing Logic")
    print("=" * 70)
    print()

    routing_info = """
Phase Transitions:
  pre_market → session_open (when market opens)
  session_open → active_trading (when trend defined)
  active_trading → post_market (when session duration exceeded)
  post_market → shutdown (when review complete)

Emergency Routing:
  Any phase → emergency_stop (when emergency detected)

Logging Routing:
  After logging → check_phase (continue cycle)
  After logging in shutdown → END (terminate)
"""
    print(routing_info)

    # Show configuration
    print("=" * 70)
    print("Configuration")
    print("=" * 70)
    print()

    print(f"Session Config:")
    for key, value in config['session_config'].items():
        print(f"  {key}: {value}")
    print()

    print(f"Risk Config:")
    for key, value in config['risk_config'].items():
        print(f"  {key}: {value}")
    print()

    print(f"Account Config:")
    for key, value in config['account_config'].items():
        print(f"  {key}: {value}")
    print()

    print("✅ Workflow inspection complete!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

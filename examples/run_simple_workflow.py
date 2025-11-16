#!/usr/bin/env python
"""
Simple Workflow Runner
Demonstrates basic LangGraph workflow execution
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import MasterOrchestrator


async def main():
    """Run a simple workflow demonstration"""

    print("=" * 70)
    print("YTC Trading System - Simple Workflow Demo")
    print("=" * 70)
    print()

    # Configuration
    config = {
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY', 'test-key'),
        'session_config': {
            'market': 'crypto',
            'instrument': 'ETH/USD',
            'duration_hours': 1  # Short demo
        },
        'risk_config': {
            'risk_per_trade_pct': 1.0,
            'max_session_risk_pct': 3.0,
            'max_positions': 3
        },
        'account_config': {
            'initial_balance': 100000.0
        }
    }

    print("📋 Configuration:")
    print(f"  Market: {config['session_config']['market']}")
    print(f"  Instrument: {config['session_config']['instrument']}")
    print(f"  Initial Balance: ${config['account_config']['initial_balance']:,.2f}")
    print(f"  Risk per Trade: {config['risk_config']['risk_per_trade_pct']}%")
    print()

    # Create orchestrator
    print("🔧 Initializing Master Orchestrator...")
    orchestrator = MasterOrchestrator(config)
    print(f"✅ Loaded {len(orchestrator.agents)} agents")
    print()

    # Start session
    print("🚀 Starting trading session...")
    session_id = await orchestrator.start_session()
    print(f"✅ Session started: {session_id}")
    print()

    # Get initial state
    state = orchestrator.get_state()
    print(f"📊 Initial Phase: {state['phase']}")
    print()

    # Process a few cycles to demonstrate workflow
    print("⚙️  Processing workflow cycles...")
    for i in range(5):
        print(f"\n--- Cycle {i+1} ---")

        await orchestrator.process_cycle()

        # Get current state
        state = orchestrator.get_state()
        print(f"Phase: {state['phase']}")
        print(f"Agents executed: {len(state['agent_outputs'])}")

        # Show which agents have run
        if state['agent_outputs']:
            latest_agents = list(state['agent_outputs'].keys())[-3:]
            print(f"Recent agents: {', '.join(latest_agents)}")

        # Show any alerts
        if state['alerts']:
            print(f"⚠️  Alerts: {len(state['alerts'])}")
            for alert in state['alerts'][-2:]:
                print(f"   - {alert['severity']}: {alert['message']}")

        await asyncio.sleep(1)

    print()
    print("=" * 70)
    print("📈 Session Summary")
    print("=" * 70)

    summary = orchestrator.get_session_summary()
    print(f"Session ID: {summary['session_id']}")
    print(f"Phase: {summary['phase']}")
    print(f"Duration: {summary['duration']:.2f} hours")
    print(f"P&L: ${summary['pnl']:.2f} ({summary['pnl_pct']:.2f}%)")
    print(f"Trades: {summary['trades']}")
    print(f"Open Positions: {summary['positions']}")
    print(f"Alerts: {summary['alerts']}")
    print()

    print("✅ Workflow demonstration complete!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

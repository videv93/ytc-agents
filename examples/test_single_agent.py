#!/usr/bin/env python
"""
Test Single Agent
Demonstrates how to run and test individual agents
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.risk_management import RiskManagementAgent
from agents.base import TradingState


async def test_risk_management():
    """Test the Risk Management Agent"""

    print("=" * 70)
    print("Testing Risk Management Agent")
    print("=" * 70)
    print()

    # Agent configuration
    config = {
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY', 'test-key'),
        'risk_config': {
            'risk_per_trade_pct': 1.0,
            'max_session_risk_pct': 3.0,
            'max_positions': 3,
            'consecutive_loss_limit': 5
        }
    }

    # Initialize agent
    print("🔧 Initializing Risk Management Agent...")
    agent = RiskManagementAgent('risk_mgmt', config)
    print("✅ Agent initialized")
    print()

    # Create test state
    state: TradingState = {
        'session_id': 'test-session-123',
        'phase': 'pre_market',
        'start_time': '2024-01-01T09:00:00',
        'current_time': '2024-01-01T09:30:00',
        'account_balance': 100000.0,
        'initial_balance': 100000.0,
        'session_pnl': 0.0,
        'session_pnl_pct': 0.0,
        'risk_per_trade_pct': 1.0,
        'max_session_risk_pct': 3.0,
        'risk_params': {},
        'risk_utilization': 0.0,
        'market': 'crypto',
        'instrument': 'ETH-USDT',
        'market_structure': {},
        'trend': {},
        'strength_weakness': {},
        'positions': [],
        'open_positions_count': 0,
        'pending_orders': [],
        'trades_today': [],
        'agent_outputs': {
            'system_init': {
                'result': {
                    'status': 'success',
                    'checks': {
                        'instrument': {
                            'specs': {
                                'tick_size': 0.0001,
                                'tick_value': 10.0,
                                'contract_size': 100000,
                                'min_size': 1000,
                                'max_size': 1000000
                            }
                        }
                    }
                }
            }
        },
        'alerts': [],
        'system_health': {'status': 'healthy'},
        'emergency_stop': False,
        'stop_reason': None
    }

    print("📊 Test State:")
    print(f"  Account Balance: ${state['account_balance']:,.2f}")
    print(f"  Risk per Trade: {state['risk_per_trade_pct']}%")
    print(f"  Max Session Risk: {state['max_session_risk_pct']}%")
    print()

    # Execute agent
    print("⚙️  Executing agent...")
    result = await agent.execute(state)
    print("✅ Execution complete")
    print()

    # Display results
    print("📈 Agent Output:")
    print(f"  Status: {result.get('status', 'unknown')}")

    if result.get('status') == 'success':
        risk_params = result.get('risk_parameters', {})
        print("\n  Risk Parameters:")
        print(f"    Risk per trade: ${risk_params.get('risk_per_trade_dollars', 0):,.2f}")
        print(f"    Max session risk: ${risk_params.get('max_session_risk_dollars', 0):,.2f}")
        print(f"    Max positions: {risk_params.get('max_positions', 0)}")

        session_risk = result.get('session_risk', {})
        print("\n  Session Risk:")
        print(f"    Open positions: {session_risk.get('open_positions', 0)}")
        print(f"    Risk utilization: {session_risk.get('risk_utilization_pct', 0):.1f}%")

        risk_checks = result.get('risk_checks', {})
        print("\n  Risk Checks:")
        print(f"    Can trade: {risk_checks.get('can_trade', False)}")
        if not risk_checks.get('can_trade'):
            print(f"    Reason: {risk_checks.get('reason', 'N/A')}")

    print()

    # Test position sizing
    print("=" * 70)
    print("Testing Position Sizing Calculation")
    print("=" * 70)
    print()

    print("📊 Trade Parameters:")
    # Mock prices for demonstration
    entry_price = 1.2500
    stop_price = 1.2475
    print(f"  Entry: {entry_price}")
    print(f"  Stop: {stop_price}")
    print(f"  Stop Distance: {abs(entry_price - stop_price)} ({abs(entry_price - stop_price) * 10000:.0f} pips)")
    print()

    position_data = agent.calculate_position_size(
        account_balance=100000.0,
        entry_price=entry_price,
        stop_price=stop_price,
        instrument_spec={
            'tick_size': 0.0001,
            'tick_value': 10.0,
            'contract_size': 100000,
            'min_size': 1000,
            'max_size': 1000000
        },
        risk_pct=1.0
    )

    print("📈 Position Sizing Result:")
    print(f"  Position Size: {position_data['position_size_contracts']:,} units")
    print(f"  Position Size: {position_data['position_size_lots']:.2f} lots")
    print(f"  Target Risk: ${position_data['risk_amount_target']:,.2f}")
    print(f"  Actual Risk: ${position_data['risk_amount_actual']:,.2f}")
    print(f"  Risk %: {position_data['risk_pct_actual']:.2f}%")
    print()

    print("✅ All tests complete!")


if __name__ == "__main__":
    try:
        asyncio.run(test_risk_management())
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

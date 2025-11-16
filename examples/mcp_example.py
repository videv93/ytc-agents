"""
Example: Using MCP Integration with Hummingbot

This example demonstrates how to use the MCP (Model Context Protocol)
integration to interact with Hummingbot Gateway for trading operations.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.system_init import SystemInitAgent
from agents.entry_execution import EntryExecutionAgent
from agents.exit_execution import ExitExecutionAgent
from agents.base import TradingState
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_initial_state() -> TradingState:
    """Create initial trading state for testing"""
    return TradingState(
        # Session Info
        session_id='demo-session-001',
        phase='pre_market',
        start_time=datetime.utcnow().isoformat(),
        current_time=datetime.utcnow().isoformat(),

        # Account State
        account_balance=100000.0,
        initial_balance=100000.0,
        session_pnl=0.0,
        session_pnl_pct=0.0,

        # Risk Management
        risk_params={
            'max_session_risk_pct': 2.0,
            'risk_per_trade_pct': 0.5,
            'max_daily_trades': 3
        },
        risk_utilization=0.0,
        max_session_risk_pct=2.0,
        risk_per_trade_pct=0.5,

        # Market State
        market='FOREX',
        instrument='GBP/USD',
        market_structure={},
        trend={},
        strength_weakness={},

        # Trading State
        positions=[],
        open_positions_count=0,
        pending_orders=[],
        trades_today=[],

        # Agent Outputs
        agent_outputs={},

        # Alerts & Monitoring
        alerts=[],
        system_health={},

        # Emergency
        emergency_stop=False,
        stop_reason=None
    )


def create_agent_config() -> dict:
    """Create configuration for agents"""
    return {
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'model': 'claude-sonnet-4-20250514',
        'max_tokens': 4096,
        'mcp_enabled': True,
        'connector': 'oanda',
        'hummingbot_gateway_url': 'http://localhost:15888',
        'timeout_seconds': 60,
        'retry_attempts': 3,
        'agent_config': {
            'entry_execution': {
                'use_limit_orders': True,
                'entry_offset_ticks': 2,
                'max_entry_attempts': 3
            },
            'exit_execution': {
                'exit_types': ['target', 'stop', 'time', 'signal']
            }
        },
        'account_config': {
            'initial_balance': 100000.0
        }
    }


async def example_1_system_initialization():
    """
    Example 1: System Initialization with MCP

    Demonstrates:
    - Checking gateway health
    - Verifying connector status
    - Getting account balance
    """
    print("\n" + "="*60)
    print("Example 1: System Initialization with MCP")
    print("="*60)

    # Create configuration and state
    config = create_agent_config()
    state = create_initial_state()

    # Initialize SystemInitAgent
    agent = SystemInitAgent('system_init', config)

    # Execute initialization
    print("\n🔄 Executing system initialization...")
    updated_state = await agent.execute(state)

    # Extract results
    agent_output = updated_state['agent_outputs']['system_init']
    result = agent_output['result']

    # Display results
    print("\n✅ System Initialization Complete!")
    print(f"  Status: {agent_output['status']}")

    print("\n📊 Health Checks:")
    for check_name, check_result in result['checks'].items():
        status_emoji = "✅" if check_result['status'] == 'ok' else "❌"
        print(f"  {status_emoji} {check_name}: {check_result['status']}")

        if check_name == 'hummingbot':
            print(f"     Gateway URL: {check_result.get('gateway_url')}")
            print(f"     Connected: {check_result.get('connected')}")
            print(f"     MCP Mode: {check_result.get('mcp_mode')}")

        elif check_name == 'broker':
            print(f"     Broker: {check_result.get('broker')}")
            print(f"     API Status: {check_result.get('api_status')}")
            print(f"     MCP Mode: {check_result.get('mcp_mode')}")

        elif check_name == 'balance':
            print(f"     Balance: ${check_result.get('balance', 0):,.2f}")
            print(f"     Currency: {check_result.get('currency', 'N/A')}")
            print(f"     MCP Mode: {check_result.get('mcp_mode')}")

    print(f"\n🎯 System Ready: {result['system_ready']}")
    print(f"💰 Account Balance: ${updated_state['account_balance']:,.2f}")


async def example_2_place_order():
    """
    Example 2: Place Entry Order with MCP

    Demonstrates:
    - Placing a market or limit order
    - Using MCP for order execution
    - Handling order results
    """
    print("\n" + "="*60)
    print("Example 2: Place Entry Order with MCP")
    print("="*60)

    # Create configuration and state with a setup
    config = create_agent_config()
    state = create_initial_state()

    # Add mock setup scanner output
    state['agent_outputs']['setup_scanner'] = {
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'success',
        'result': {
            'setups': [{
                'type': 'pullback',
                'direction': 'long',
                'quality': 0.85,
                'entry_zone': {
                    'high': 1.2520,
                    'low': 1.2500
                },
                'setup_location': 1.2510
            }]
        }
    }

    # Add mock risk management output
    state['agent_outputs']['risk_management'] = {
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'success'
    }

    # Initialize EntryExecutionAgent
    agent = EntryExecutionAgent('entry_execution', config)

    # Execute entry logic
    print("\n🔄 Checking for entry opportunity...")
    updated_state = await agent.execute(state)

    # Extract results
    agent_output = updated_state['agent_outputs']['entry_execution']
    result = agent_output['result']

    # Display results
    print(f"\n📈 Entry Execution Result:")
    print(f"  Status: {result['status']}")

    if result['status'] == 'executed':
        order = result['order']
        print(f"\n✅ Order Placed Successfully!")
        print(f"  Order ID: {order['order_id']}")
        print(f"  Connector: {order.get('connector', 'N/A')}")
        print(f"  Trading Pair: {order.get('trading_pair', 'N/A')}")
        print(f"  Side: {order.get('side', 'N/A')}")
        print(f"  Amount: {order.get('amount', 0)} lots")
        print(f"  Order Type: {order.get('order_type', 'N/A')}")
        print(f"  Execution Price: {order.get('execution_price', 0):.4f}")
        print(f"  MCP Mode: {order.get('mcp_mode', 'N/A')}")

    elif result['status'] == 'waiting':
        print(f"\n⏳ Waiting for entry trigger")
        print(f"  Setup: {result['setup']['type']}")
        print(f"  Waiting for: {result['waiting_for']}")

    elif result['status'] == 'rejected':
        print(f"\n❌ Entry Rejected")
        print(f"  Reason: {result['reason']}")


async def example_3_close_position():
    """
    Example 3: Close Position with MCP

    Demonstrates:
    - Closing an open position
    - Using MCP for exit execution
    - Handling exit results
    """
    print("\n" + "="*60)
    print("Example 3: Close Position with MCP")
    print("="*60)

    # Create configuration and state with an open position
    config = create_agent_config()
    state = create_initial_state()

    # Add mock open position
    state['positions'] = [{
        'id': 'POS-001',
        'direction': 'long',
        'instrument': 'GBP/USD',
        'entry_price': 1.2500,
        'position_size_lots': 1.0,
        'stop_loss': 1.2450,
        'take_profit': 1.2600,
        'current_price': 1.2550,
        'pnl': 50.0,
        'entry_time': datetime.utcnow().isoformat()
    }]
    state['open_positions_count'] = 1

    # Initialize ExitExecutionAgent
    agent = ExitExecutionAgent('exit_execution', config)

    # Execute exit logic
    print("\n🔄 Checking for exit signals...")
    updated_state = await agent.execute(state)

    # Extract results
    agent_output = updated_state['agent_outputs']['exit_execution']
    result = agent_output['result']

    # Display results
    print(f"\n📉 Exit Execution Result:")
    print(f"  Status: {result['status']}")

    if result.get('exits'):
        for exit_info in result['exits']:
            print(f"\n✅ Position Closed!")
            print(f"  Position ID: {exit_info.get('position_id', 'N/A')}")
            print(f"  Exit Type: {exit_info.get('exit_type', 'N/A')}")
            print(f"  Exit Price: {exit_info.get('exit_price', 0):.4f}")
            print(f"  Reason: {exit_info.get('reason', 'N/A')}")
            print(f"  Order ID: {exit_info.get('order_id', 'N/A')}")
            print(f"  MCP Mode: {exit_info.get('mcp_mode', 'N/A')}")
    else:
        print("\n⏸️  No exit signals detected")


async def example_4_direct_mcp_client():
    """
    Example 4: Direct MCP Client Usage

    Demonstrates:
    - Using HummingbotMCPClient directly
    - Calling individual MCP tools
    - Lower-level MCP operations
    """
    print("\n" + "="*60)
    print("Example 4: Direct MCP Client Usage")
    print("="*60)

    from tools.mcp_client import HummingbotMCPClient
    from anthropic import Anthropic

    # Initialize MCP client
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set. Skipping this example.")
        return

    client = Anthropic(api_key=api_key)
    mcp_client = HummingbotMCPClient(client, model="claude-sonnet-4-20250514")

    print("\n📊 Available Tools:")
    for i, tool in enumerate(mcp_client.tools, 1):
        print(f"  {i}. {tool['name']}: {tool['description'][:60]}...")

    # Example: Check gateway status
    print("\n🔍 Checking Gateway Status...")
    try:
        status = await mcp_client.check_gateway_status()
        print(f"  Result: {status}")
    except Exception as e:
        print(f"  Error: {e}")

    # Example: Get balance
    print("\n💰 Getting Account Balance...")
    try:
        balance = await mcp_client.get_balance(connector="oanda")
        print(f"  Result: {balance}")
    except Exception as e:
        print(f"  Error: {e}")

    # Example: Get market data
    print("\n📈 Getting Market Data...")
    try:
        market_data = await mcp_client.get_market_data(
            connector="oanda",
            trading_pair="GBP/USD"
        )
        print(f"  Result: {market_data}")
    except Exception as e:
        print(f"  Error: {e}")


async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("MCP Integration Examples")
    print("="*60)
    print("\nThese examples demonstrate the MCP integration with Hummingbot.")
    print("Note: Examples will use mock data if Hummingbot Gateway is not running.")

    try:
        # Run examples
        await example_1_system_initialization()
        await asyncio.sleep(1)

        await example_2_place_order()
        await asyncio.sleep(1)

        await example_3_close_position()
        await asyncio.sleep(1)

        await example_4_direct_mcp_client()

        print("\n" + "="*60)
        print("All Examples Completed!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

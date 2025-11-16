# YTC Trading System - Examples

Practical examples to help you understand and run the LangGraph workflow.

## Quick Start

### 1. Inspect the Workflow Structure

```bash
python examples/inspect_workflow.py
```

This shows:
- All registered agents
- Workflow phases
- State structure
- Routing logic

**No API key required** - uses test configuration.

### 2. Test a Single Agent

```bash
python examples/test_single_agent.py
```

Demonstrates:
- How to initialize an agent
- How to create test state
- How to execute an agent
- How to inspect results
- Position sizing calculations

**No API key required** - works with mock data.

### 3. Run Simple Workflow

```bash
# Set your API key first (optional for demo)
export ANTHROPIC_API_KEY="sk-ant-..."

python examples/run_simple_workflow.py
```

Demonstrates:
- Full orchestrator initialization
- Session startup
- Multi-cycle execution
- Phase transitions
- Session summary

**API key optional** - will use test key if not set, some agents may have limited functionality.

## Examples

### Example 1: Inspect Workflow

```bash
$ python examples/inspect_workflow.py

======================================================================
YTC Trading System - Workflow Structure
======================================================================

🔧 Initializing orchestrator...

📋 Registered Agents:

   1. system_init              - SystemInitAgent
   2. risk_mgmt                - RiskManagementAgent
   3. market_structure         - MarketStructureAgent
   ...
  17. logging_audit            - LoggingAuditAgent

======================================================================
Workflow Phases
======================================================================

PRE-MARKET:
  ✅ system_init
  ✅ risk_mgmt
  ✅ market_structure
  ✅ economic_calendar
  ...
```

### Example 2: Test Single Agent

```bash
$ python examples/test_single_agent.py

======================================================================
Testing Risk Management Agent
======================================================================

🔧 Initializing Risk Management Agent...
✅ Agent initialized

📊 Test State:
  Account Balance: $100,000.00
  Risk per Trade: 1.0%
  Max Session Risk: 3.0%

⚙️  Executing agent...
✅ Execution complete

📈 Agent Output:
  Status: success

  Risk Parameters:
    Risk per trade: $1,000.00
    Max session risk: $3,000.00
    Max positions: 3

  Session Risk:
    Open positions: 0
    Risk utilization: 0.0%

  Risk Checks:
    Can trade: True

======================================================================
Testing Position Sizing Calculation
======================================================================

📊 Trade Parameters:
  Entry: 1.25
  Stop: 1.2475
  Stop Distance: 0.0025 (25 pips)

📈 Position Sizing Result:
  Position Size: 400,000 units
  Position Size: 4.00 lots
  Target Risk: $1,000.00
  Actual Risk: $1,000.00
  Risk %: 1.00%

✅ All tests complete!
```

### Example 3: Run Workflow

```bash
$ python examples/run_simple_workflow.py

======================================================================
YTC Trading System - Simple Workflow Demo
======================================================================

📋 Configuration:
   Market: crypto
   Instrument: ETH/USD
  Initial Balance: $100,000.00
  Risk per Trade: 1.0%

🔧 Initializing Master Orchestrator...
✅ Loaded 17 agents

🚀 Starting trading session...
✅ Session started: a1b2c3d4-e5f6-7890-1234-567890abcdef

📊 Initial Phase: pre_market

⚙️  Processing workflow cycles...

--- Cycle 1 ---
Phase: pre_market
Agents executed: 4
Recent agents: system_init, risk_mgmt, market_structure

--- Cycle 2 ---
Phase: pre_market
Agents executed: 5
Recent agents: market_structure, economic_calendar, contingency
...

======================================================================
📈 Session Summary
======================================================================
Session ID: a1b2c3d4-e5f6-7890-1234-567890abcdef
Phase: active_trading
Duration: 0.01 hours
P&L: $0.00 (0.00%)
Trades: 0
Open Positions: 0
Alerts: 0

✅ Workflow demonstration complete!
```

## Understanding the Output

### Agent Execution Flow

Each cycle, you'll see:
1. **Phase**: Current workflow phase
2. **Agents executed**: Total number of agents that have run
3. **Recent agents**: Last few agents that executed
4. **Alerts**: Any warnings or issues

### Phase Transitions

The workflow moves through phases:
- **pre_market**: System initialization, risk setup, structure analysis
- **session_open**: Trend definition, strength analysis
- **active_trading**: Setup scanning, trade execution, management
- **post_market**: Review, analytics, learning
- **shutdown**: Cleanup and final reporting

### State Updates

Each agent updates the shared `TradingState`:
- `agent_outputs`: Stores each agent's results
- `positions`: Tracks open trades
- `alerts`: Warning and error messages
- `phase`: Current workflow phase

## Customization

### Modify Configuration

Edit the `config` dictionary in any example:

```python
config = {
    'anthropic_api_key': 'your-key',
    'session_config': {
        'market': 'forex',
        'instrument': 'EUR/USD',  # Change instrument
        'duration_hours': 2        # Change duration
    },
    'risk_config': {
        'risk_per_trade_pct': 0.5,  # More conservative
        'max_session_risk_pct': 2.0,
        'max_positions': 2
    },
    'account_config': {
        'initial_balance': 50000.0  # Smaller account
    }
}
```

### Test Different Scenarios

Create test states with different conditions:

```python
# Test with losing positions
state['positions'] = [
    {'pnl': -100, 'direction': 'long'},
    {'pnl': -150, 'direction': 'short'}
]
state['session_pnl'] = -250
state['session_pnl_pct'] = -0.25

# Test emergency conditions
state['session_pnl_pct'] = -3.0  # Trigger stop loss
```

### Run Specific Phases

Modify the orchestrator to start at a specific phase:

```python
# In run_simple_workflow.py
orchestrator.session_state['phase'] = 'active_trading'
```

## Troubleshooting

### ImportError

```bash
# Ensure you're in the project root
cd /path/to/ytc-agents

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Module Not Found

```bash
# The examples add the project root to sys.path automatically
# If issues persist, run from project root:
cd /path/to/ytc-agents
python -m examples.run_simple_workflow
```

### API Key Issues

The examples work without an API key using mock data. If you want full functionality:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or add to `.env` file:
```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
```

## Next Steps

1. **Run all examples** to understand the system
2. **Modify configurations** to test different scenarios
3. **Create custom test scripts** for your use cases
4. **Review agent outputs** in the logs
5. **Run the full system** with `python main.py`

## Additional Resources

- **Documentation**: `docs/RUNNING_THE_SYSTEM.md`
- **Agent Summary**: `docs/AGENTS_SUMMARY.md`
- **Implementation Guide**: `docs/IMPLEMENTATION_GUIDE.md`
- **Setup Guide**: `README_SETUP.md`

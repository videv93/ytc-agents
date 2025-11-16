# Running the YTC Trading System with LangGraph

## Quick Start

### 1. Setup Environment

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Run the System

```bash
# Run the complete system
python main.py
```

That's it! The system will:
1. Initialize all 17 agents
2. Build the LangGraph workflow
3. Start a trading session
4. Execute agents based on phase

## Understanding the Workflow

### Workflow Phases

The LangGraph workflow executes in phases:

```
┌─────────────────────────────────────────────────────┐
│ PRE-MARKET PHASE                                    │
│ System Init → Risk Mgmt → Market Structure →        │
│ Economic Calendar → Emergency Check                 │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ SESSION OPEN PHASE                                  │
│ Trend Definition → Strength & Weakness              │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ ACTIVE TRADING PHASE (Loop)                        │
│ Monitoring → Setup Scanner → Entry Execution →     │
│ Trade Management → Exit Execution                   │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ POST-MARKET PHASE                                   │
│ Session Review → Performance Analytics →            │
│ Learning → Next Session Prep                        │
└─────────────────────────────────────────────────────┘
```

### How LangGraph Works

LangGraph manages the workflow as a state machine:

1. **State**: `TradingState` dictionary shared across all agents
2. **Nodes**: Each agent is a node in the graph
3. **Edges**: Define the flow between agents
4. **Conditional Edges**: Route based on state (phase, emergency status, etc.)

## Running Options

### Option 1: Full System (Production)

```bash
python main.py
```

This runs the complete workflow with all agents.

### Option 2: Test Individual Agents

Create a test script to run a single agent:

```python
# test_agent.py
import asyncio
from agents.risk_management import RiskManagementAgent
from agents.base import TradingState

async def test_risk_agent():
    config = {
        'anthropic_api_key': 'your-key-here',
        'risk_config': {
            'risk_per_trade_pct': 1.0,
            'max_session_risk_pct': 3.0,
            'max_positions': 3
        }
    }

    agent = RiskManagementAgent('risk_mgmt', config)

    # Create mock state
    state: TradingState = {
        'session_id': 'test-123',
        'account_balance': 100000.0,
        'session_pnl': 0.0,
        'session_pnl_pct': 0.0,
        'positions': [],
        'trades_today': [],
        'risk_per_trade_pct': 1.0,
        'max_session_risk_pct': 3.0,
        'agent_outputs': {
            'system_init': {
                'result': {
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
        }
    }

    # Execute agent
    result = await agent.execute(state)
    print(f"Agent Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_risk_agent())
```

Run it:
```bash
python test_agent.py
```

### Option 3: Step Through Workflow Manually

```python
# manual_workflow.py
import asyncio
from agents.orchestrator import MasterOrchestrator
import yaml

async def step_through_workflow():
    # Load config
    config = {
        'anthropic_api_key': 'your-key',
        'session_config': {
            'market': 'forex',
            'instrument': 'GBP/USD'
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

    # Create orchestrator
    orchestrator = MasterOrchestrator(config)

    # Start session
    session_id = await orchestrator.start_session()
    print(f"Session Started: {session_id}")

    # Process a few cycles
    for i in range(3):
        print(f"\n--- Cycle {i+1} ---")
        await orchestrator.process_cycle()

        # Check current state
        state = orchestrator.get_state()
        print(f"Phase: {state['phase']}")
        print(f"Agent Outputs: {list(state['agent_outputs'].keys())}")

        await asyncio.sleep(2)

    # Get summary
    summary = orchestrator.get_session_summary()
    print(f"\nSession Summary: {summary}")

if __name__ == "__main__":
    asyncio.run(step_through_workflow())
```

Run it:
```bash
python manual_workflow.py
```

## Visualizing the Workflow

### Option 1: LangGraph Studio (Recommended)

LangGraph has a built-in visualization tool:

```bash
# Install LangGraph CLI
pip install langgraph-cli

# Start the studio
langgraph dev
```

Then open http://localhost:8000 in your browser to see the visual workflow.

### Option 2: Export to Mermaid Diagram

```python
# visualize_workflow.py
from agents.orchestrator import MasterOrchestrator

config = {
    'anthropic_api_key': 'test',
    'session_config': {},
    'risk_config': {},
    'account_config': {'initial_balance': 100000}
}

orchestrator = MasterOrchestrator(config)

# Get the workflow graph
graph = orchestrator.workflow

# Print mermaid diagram
print(graph.get_graph().draw_mermaid())
```

This will output a Mermaid diagram you can paste into documentation.

## Configuration

### Minimal Configuration

```python
# minimal_config.py
config = {
    'anthropic_api_key': 'sk-ant-...',
    'session_config': {
        'market': 'forex',
        'instrument': 'GBP/USD'
    },
    'risk_config': {
        'risk_per_trade_pct': 1.0,
        'max_session_risk_pct': 3.0
    },
    'account_config': {
        'initial_balance': 100000.0
    }
}
```

### Full Configuration (from YAML files)

```python
# Load from config files
import yaml

with open('config/session_config.yaml') as f:
    session_config = yaml.safe_load(f)

with open('config/risk_config.yaml') as f:
    risk_config = yaml.safe_load(f)

with open('config/agent_config.yaml') as f:
    agent_config = yaml.safe_load(f)

config = {
    'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
    'session_config': session_config,
    'risk_config': risk_config,
    'agent_config': agent_config,
    'account_config': {
        'initial_balance': float(os.getenv('INITIAL_BALANCE', 100000))
    }
}
```

## Debugging the Workflow

### Enable Debug Logging

```python
# Set log level to DEBUG in .env
LOG_LEVEL=DEBUG

# Or in code:
import structlog
import logging

logging.basicConfig(level=logging.DEBUG)
```

### Check Agent Execution

Each agent logs its execution:

```python
# View logs
tail -f logs/ytc_system.log

# Or in Python
import structlog
logger = structlog.get_logger()
logger.info("checking_agent_output", agent="risk_mgmt")
```

### Inspect State at Any Point

```python
# Get current state
state = orchestrator.get_state()

# Check specific agent output
risk_output = state['agent_outputs'].get('risk_mgmt')
print(risk_output)

# Check phase
print(f"Current phase: {state['phase']}")

# Check positions
print(f"Open positions: {state['positions']}")
```

### Trace Workflow Execution

```python
# Add callbacks to trace execution
from langchain.callbacks import StdOutCallbackHandler

# The workflow automatically logs, but you can add more
orchestrator.workflow.invoke(
    orchestrator.session_state,
    config={"callbacks": [StdOutCallbackHandler()]}
)
```

## Common Issues & Solutions

### Issue 1: ImportError for LangGraph

```bash
# Solution: Install correct version
pip install langgraph>=0.0.40
```

### Issue 2: Anthropic API Key Not Found

```bash
# Solution: Set environment variable
export ANTHROPIC_API_KEY="sk-ant-..."

# Or add to .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
```

### Issue 3: Workflow Hangs

```python
# Solution: Check for infinite loops in phase transitions
# Add timeout to workflow execution

import asyncio

async def run_with_timeout():
    try:
        await asyncio.wait_for(
            orchestrator.run(),
            timeout=300  # 5 minutes
        )
    except asyncio.TimeoutError:
        print("Workflow timed out")
        await orchestrator.emergency_shutdown("Timeout")
```

### Issue 4: Agent Execution Fails

```python
# Solution: Check agent outputs for errors
state = orchestrator.get_state()
for agent_id, output in state['agent_outputs'].items():
    if output.get('status') == 'error':
        print(f"Agent {agent_id} failed: {output.get('error')}")
```

## Testing the Workflow

### Unit Test Individual Agents

```python
# tests/test_workflow.py
import pytest
from agents.orchestrator import MasterOrchestrator

@pytest.mark.asyncio
async def test_workflow_initialization():
    config = get_test_config()
    orchestrator = MasterOrchestrator(config)
    assert orchestrator.workflow is not None
    assert len(orchestrator.agents) == 17

@pytest.mark.asyncio
async def test_pre_market_phase():
    config = get_test_config()
    orchestrator = MasterOrchestrator(config)

    # Start session
    session_id = await orchestrator.start_session()

    # Check pre-market agents executed
    state = orchestrator.get_state()
    assert 'system_init' in state['agent_outputs']
    assert 'risk_mgmt' in state['agent_outputs']
```

Run tests:
```bash
pytest tests/test_workflow.py -v
```

### Integration Test Full Workflow

```python
# tests/integration/test_full_workflow.py
import pytest
from agents.orchestrator import MasterOrchestrator

@pytest.mark.asyncio
async def test_full_session_cycle():
    orchestrator = MasterOrchestrator(get_test_config())

    # Run complete session
    session_id = await orchestrator.start_session()

    # Simulate market cycles
    for _ in range(10):
        await orchestrator.process_cycle()

    # Check all phases executed
    state = orchestrator.get_state()
    assert state['phase'] in ['active_trading', 'post_market', 'shutdown']
```

## Advanced Usage

### Custom Agent Execution Order

You can modify the workflow in `orchestrator.py` to change execution order:

```python
# In _build_workflow method
workflow.add_edge("custom_agent", "next_agent")
```

### Conditional Agent Execution

Add conditional logic:

```python
def should_run_agent(state: TradingState) -> bool:
    # Custom logic
    return state.get('some_condition') == True

workflow.add_conditional_edges(
    "agent_name",
    should_run_agent,
    {True: "run_agent", False: "skip_agent"}
)
```

### Parallel Agent Execution

Currently agents run sequentially, but you can parallelize:

```python
from langgraph.prebuilt import ParallelNode

# Run multiple agents in parallel
parallel_agents = ParallelNode([
    agent1.execute,
    agent2.execute,
    agent3.execute
])

workflow.add_node("parallel_analysis", parallel_agents)
```

## Monitoring in Production

### Check Workflow Status

```python
# Get current status
summary = orchestrator.get_session_summary()
print(f"""
Session: {summary['session_id']}
Phase: {summary['phase']}
Duration: {summary['duration']:.2f}h
P&L: ${summary['pnl']:.2f} ({summary['pnl_pct']:.2f}%)
Trades: {summary['trades']}
Positions: {summary['positions']}
Alerts: {summary['alerts']}
""")
```

### Real-time Dashboard

Access metrics via the monitoring agent:

```python
# In your dashboard code
state = orchestrator.get_state()
monitoring_output = state['agent_outputs'].get('monitoring', {})

# Display metrics
metrics = monitoring_output.get('result', {})
print(f"System Status: {metrics.get('system_status')}")
print(f"Alerts: {metrics.get('alerts_generated')}")
```

## Next Steps

1. **Start with Manual Testing**: Run `manual_workflow.py` to understand the flow
2. **Test Individual Agents**: Verify each agent works independently
3. **Run Full System**: Execute `main.py` with paper trading
4. **Monitor Logs**: Watch `logs/ytc_system.log` for execution details
5. **Integrate Live Data**: Replace mock data with actual market feeds
6. **Deploy to Production**: Use Docker Compose for reliable deployment

---

**Need Help?**
- Check the logs: `tail -f logs/ytc_system.log`
- Review agent outputs in the database
- Use LangGraph Studio for visual debugging
- Test agents individually before running full workflow

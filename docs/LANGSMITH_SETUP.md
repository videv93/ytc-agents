# LangSmith Setup Guide

Use LangSmith to visualize, trace, and debug the YTC Trading System's LangGraph workflow.

## Quick Start

### 1. Get LangSmith API Key

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Create a free account
3. Navigate to Settings → API Keys
4. Copy your API key

### 2. Configure Environment

Add to your `.env` file:

```bash
LANGSMITH_API_KEY=your_api_key_here
LANGSMITH_PROJECT=ytc-trading-system
```

### 3. Install LangSmith

```bash
pip install langsmith>=0.1.0
```

The package is already in `requirements.txt`, so:

```bash
pip install -e .
```

## Viewing the Workflow Graph

### Option A: Local Visualization

Generate and save a PNG visualization locally:

```bash
python3 examples/visualize_workflow.py --output graphs/workflow.png
```

This creates a visual representation of:
- All 17 agents
- Phase transitions (pre_market → session_open → active_trading → post_market → shutdown)
- Routing logic and conditional flows
- Continuous monitoring agents

### Option B: ASCII Graph (No Dependencies)

View the graph in ASCII format without graphviz:

```bash
python3 examples/visualize_workflow.py --ascii
```

### Option C: LangSmith Dashboard

Enable real-time tracing in LangSmith:

```bash
python3 examples/visualize_workflow.py --langsmith
```

Then visit: `https://smith.langchain.com/projects/ytc-trading-system`

## Automatic Tracing During Trading Sessions

Once LangSmith is configured, it automatically traces all trading sessions:

1. Run the system normally:
   ```bash
   python3 main.py
   ```

2. LangSmith will automatically capture:
   - Agent execution traces
   - State transitions
   - Claude API calls and responses
   - Performance metrics
   - Errors and warnings

3. View traces at: `https://smith.langchain.com/projects/ytc-trading-system`

## What Gets Traced

### LangGraph Execution
- Agent transitions between nodes
- State mutations at each step
- Routing decisions
- Execution duration

### LLM Calls
- All Claude API requests (prompts + responses)
- Token usage
- Temperature and other parameters

### State Flow
- Trading state at each phase
- Position updates
- P&L calculations
- Risk metrics

### Errors
- Agent failures
- API errors
- Warning logs

## LangSmith Features

### Run History
View complete execution traces with:
- Timeline of agent execution
- State changes at each node
- Token usage statistics
- Latency breakdown

### Comparison
Compare multiple trading sessions:
- Different market conditions
- Strategy performance
- Agent decision patterns

### Feedback
Add feedback to runs:
- Mark trades as successful/unsuccessful
- Add notes for analysis
- Create datasets for fine-tuning

### Datasets
Create datasets from successful runs:
- Use as training data for prompt optimization
- Analyze patterns in profitable trades
- Build feedback loops

## Debugging with LangSmith

### Trace Agent Decisions
1. Open a run in LangSmith
2. Click on specific agent nodes
3. See exact inputs and outputs
4. View full Claude conversation

### Analyze State Transitions
1. Expand each node in the trace
2. See state before and after
3. Identify unexpected mutations
4. Debug routing decisions

### Monitor Performance
1. View latency per agent
2. Identify bottlenecks
3. Monitor token usage
4. Track error rates

## Disable LangSmith

If you don't want tracing, simply don't set `LANGSMITH_API_KEY` in `.env`.

The system will work normally without any LangSmith dependencies beyond what's imported.

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `LANGSMITH_API_KEY` | Your LangSmith API key | `ls_xxxx...` |
| `LANGSMITH_PROJECT` | Project name in LangSmith | `ytc-trading-system` |
| `LANGCHAIN_TRACING_V2` | Enable tracing (auto-set) | `true` |

## Common Issues

### "graphviz not found"
If you get this error when trying to save PNG:

```bash
brew install graphviz  # macOS
apt-get install graphviz  # Linux
choco install graphviz  # Windows
```

Or use `--ascii` flag for text visualization.

### "API Key Invalid"
Verify your API key:
1. Check it's in `.env` (not `.env.example`)
2. Reload environment: `python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print('Key set' if os.getenv('LANGSMITH_API_KEY') else 'Key not found')"`
3. Check https://smith.langchain.com/settings/api-keys for valid keys

### "Tracing not working"
Ensure:
1. `LANGSMITH_API_KEY` is set in `.env`
2. Run `pip install langsmith`
3. Restart Python process

## Learn More

- [LangSmith Docs](https://docs.smith.langchain.com/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangChain Tracing](https://python.langchain.com/docs/langsmith/)

## Workflow Architecture

The YTC system uses LangGraph to orchestrate agents through trading phases:

```
┌─────────────────────────────────────────────────────────────┐
│                     MASTER ORCHESTRATOR                      │
│                    (StateGraph in LangGraph)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼────────┐  ┌──────▼───────────┐
            │  PRE_MARKET    │  │  SESSION_OPEN    │
            │   (4 agents)   │  │   (2 agents)     │
            └────────────────┘  └──────────────────┘
                    │                   │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼──────────┐
                    │  ACTIVE_TRADING    │
                    │  (4 agents, loops) │
                    └──────────┬─────────┘
                              │
                    ┌─────────▼──────────┐
                    │  POST_MARKET       │
                    │  (4 agents)        │
                    └────────────────────┘
```

Each phase runs its agents, then transitions to the next. Continuous agents (monitoring, contingency, logging) run during all phases.

LangSmith visualizes this entire flow with real execution data.

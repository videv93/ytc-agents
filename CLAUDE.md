# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YTC Automated Trading System - A multi-agent trading system implementing the YTC (Your Trading Coach) Price Action methodology by Lance Beggs. Built with LangGraph and Claude (Anthropic), this system automates the complete trading workflow from pre-market analysis through post-market review.

**Core Philosophy**: Pure price action trading with strict risk management, multi-timeframe analysis, and continuous improvement through session reviews.

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Setup environment
cp .env.example .env
# Edit .env with your configuration
```

### Running the System
```bash
# Run main trading system
python3 main.py

# Test individual agents
python3 examples/test_single_agent.py

# Run workflow examples
python3 examples/run_simple_workflow.py
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m backtest      # Backtesting tests only

# Run specific test file
pytest tests/unit/test_pivot_detection.py
pytest tests/unit/test_risk_management.py
```

### Code Quality
```bash
# Format code with Black
black .

# Sort imports
isort .

# Lint with flake8
flake8 .

# Type checking
mypy agents/ skills/ tools/
```

## Architecture

### Multi-Agent System (LangGraph)

The system uses **LangGraph** for state management and workflow orchestration. All agents share a common `TradingState` that flows through the workflow graph.

**Key Components:**

1. **MasterOrchestrator** (`agents/orchestrator.py`)
   - Central coordinator using LangGraph StateGraph
   - Routes execution through trading phases: pre_market → session_open → active_trading → post_market → shutdown
   - Manages the workflow graph and agent transitions

2. **TradingState** (`agents/base.py`)
   - TypedDict that flows through the LangGraph workflow
   - Shared state includes: session info, account balance, positions, risk params, market structure, agent outputs, alerts
   - All agents read from and write to this state

3. **BaseAgent** (`agents/base.py`)
   - Abstract base class for all agents
   - Each agent implements `execute(state: TradingState) -> TradingState`
   - Uses Anthropic Claude API for LLM reasoning
   - Has access to `HummingbotGatewayClient` for trading operations

### Agent Categories

**Pre-Market Agents:**
- `system_init.py` - System initialization and health checks
- `economic_calendar.py` - Economic event analysis
- `market_structure.py` - Market structure identification
- `trend_definition.py` - Trend analysis
- `strength_weakness.py` - Strength/weakness analysis

**Active Trading Agents:**
- `setup_scanner.py` - Trade setup identification
- `entry_execution.py` - Trade entry execution
- `trade_management.py` - Active trade management
- `exit_execution.py` - Trade exit execution
- `risk_management.py` - Real-time risk monitoring

**Support Agents:**
- `monitoring.py` - System and position monitoring
- `contingency.py` - Emergency handling
- `logging_audit.py` - Audit trail logging

**Post-Market Agents:**
- `session_review.py` - Session performance review
- `performance_analytics.py` - Detailed analytics
- `learning_optimization.py` - Strategy optimization
- `next_session_prep.py` - Next session preparation

### External Integrations

**Hummingbot Gateway API** (`tools/gateway_api_client.py`)
- Direct HTTP client for Hummingbot Gateway REST API
- Handles: market data, order placement, position management, portfolio queries
- Uses async aiohttp for all API calls
- Configure via `HUMMINGBOT_GATEWAY_URL` environment variable

**Database** (`database/connection.py`)
- PostgreSQL with SQLAlchemy ORM
- Connection pooling via QueuePool
- Models defined in `database/models.py`
- Configure via `POSTGRES_*` environment variables

**Redis** (referenced in dependencies)
- Used for state persistence and caching
- Configure via `REDIS_*` environment variables

## Configuration

The system loads configuration from multiple sources in priority order:
1. Environment variables (`.env` file)
2. YAML config files in `config/`:
   - `session_config.yaml` - Trading session parameters
   - `risk_config.yaml` - Risk management rules
   - `agent_config.yaml` - Agent-specific settings

### Required Environment Variables

```bash
ANTHROPIC_API_KEY           # Required - Claude API key
HUMMINGBOT_GATEWAY_URL      # Hummingbot Gateway endpoint
POSTGRES_HOST               # Database connection
POSTGRES_DB                 # Database name
POSTGRES_USER               # Database user
POSTGRES_PASSWORD           # Database password
```

See `.env.example` for complete configuration template.

## Skills and Tools

**Skills** (`skills/`)
- Reusable trading analysis components
- `pivot_detection.py` - Pivot point identification
- `fibonacci.py` - Fibonacci level calculations

**Tools** (`tools/`)
- `gateway_api_client.py` - Hummingbot Gateway integration

## Workflow Execution

The main entry point (`main.py`) orchestrates:
1. Load environment and configuration from `.env` + YAML files
2. Initialize database connection (`DatabaseManager`)
3. Initialize `MasterOrchestrator` with LangGraph workflow
4. Start trading session → enters main loop
5. Orchestrator processes workflow cycles through agent nodes
6. Graceful shutdown on signal (SIGINT/SIGTERM) with session summary

Each agent receives the current `TradingState`, performs its logic (often with Claude API calls), and returns an updated state that flows to the next agent in the graph.

## YTC Methodology Implementation

This system strictly follows YTC trading principles:

**Multi-Timeframe Analysis:**
- Higher Timeframe (30min): Market structure, support/resistance zones
- Trading Timeframe (3min): Trend analysis, setup identification
- Lower Timeframe (1min): Entry refinement and timing

**Risk Management Rules:**
- 1% risk per trade (strictly enforced)
- 3% maximum session loss (automatic shutdown)
- Maximum 3 simultaneous positions
- Position sizing formula: `(Account × Risk%) / (Entry - Stop) / Tick Value`

**Setup Types:**
- Pullback to Structure (primary)
- 3-Swing Trap Patterns
- Continuation Patterns
- Fibonacci entry zones (50%, 61.8%)

**Trade Management:**
- Initial stop loss at structure
- Move to breakeven at +1R
- Partial exit (50%) at Target 1
- Trailing stops at pivot points
- Time-based exits if no progress

## Important Implementation Notes

### Hummingbot Integration Status

The system includes a `HummingbotGatewayClient` in `tools/gateway_api_client.py` that communicates directly with the Hummingbot Gateway REST API (not MCP protocol). Some methods may use placeholder responses - check implementations before live trading.

**Key Integration Points:**
- Market data fetching (OHLC, tickers)
- Order placement and management
- Position monitoring
- Account balance queries
- Trading pair information

**Before Live Trading:**
1. Verify all Hummingbot API endpoints return real data
2. Test order execution in paper trading mode
3. Validate position sizing calculations
4. Confirm risk limit enforcement works

### Database Dependencies

The system requires PostgreSQL for:
- Session tracking and state persistence
- Trade history and audit logs
- Agent decision logging
- Performance analytics

Initialize database before first run:
```bash
# See database/connection.py for connection setup
# Tables are auto-created via SQLAlchemy ORM
python -c "from database.connection import DatabaseManager; db = DatabaseManager(); db.create_tables()"
```

### Testing Individual Agents

To test a single agent in isolation, use the examples:
```bash
python3 examples/test_single_agent.py
```

Modify the script to test different agents by importing and initializing them with appropriate config.

## Common Workflows

### Paper Trading Session
1. Set `ENABLE_PAPER_TRADING=true` in `.env`
2. Configure session parameters in `config/session_config.yaml`
3. Run: `python3 main.py`
4. Monitor logs: `tail -f logs/ytc_system.log`
5. Review session after completion in database

### Backtesting (Planned)
- Backtest framework is referenced but not yet fully implemented
- See `examples/` directory for framework stubs
- Will support historical data replay through agent workflow

### Emergency Shutdown
The system has multiple safety layers:
- Session stop loss at -3% (automatic)
- Connection loss detection (flattens positions)
- Manual emergency stop (Ctrl+C sends SIGINT)
- Contingency agent monitors for critical failures

## Python Version

Requires Python >= 3.10 (uses modern type hints and features)

## Additional Documentation

Comprehensive documentation is available in the `docs/` directory:

**Getting Started:**
- `docs/README.md` - Complete system overview and architecture
- `docs/IMPLEMENTATION_GUIDE.md` - Step-by-step setup with code examples
- `docs/RUNNING_THE_SYSTEM.md` - How to run and debug the LangGraph workflow

**Agent Documentation:**
- `docs/AGENTS_SUMMARY.md` - Quick reference for all 17 agents
- `docs/00_MASTER_ORCHESTRATOR.md` through `docs/17_LOGGING_AUDIT.md` - Detailed specs for each agent including input/output schemas, skills, and workflows

**Quick Reference:**
- `docs/AGENT_QUICK_REFERENCE.md` - Agent responsibilities at a glance

**Note**: The documentation references some features (like backtesting framework, Prometheus/Grafana monitoring) that may be planned but not fully implemented. Always verify code implementation against documentation claims.

# YTC Trading System - Subagent Implementation Guide

## Overview

The YTC (Your Trading Coach) Trading System has been converted to **18 Anthropic Claude subagents** that can be invoked via the Task tool. Each agent specializes in a specific aspect of the trading workflow and uses **MCP_DOCKER** tools to interact with Hummingbot API.

## Subagent Architecture

### Location
All subagents are located in: `~/.claude/agents/`

### Available Agents (18 Total)

#### Orchestration (1 agent)
- **ytc-master-orchestrator** - Coordinates all 17 trading agents through complete trading cycle

#### Pre-Market Phase (6 agents)
- **ytc-system-init** - Platform connectivity and health checks
- **ytc-risk-management** - Position sizing and risk limits (1% per trade, 3% session max)
- **ytc-market-structure** - Support/resistance zones on 30min chart
- **ytc-economic-calendar** - News filtering and trading restrictions
- **ytc-trend-definition** - Trend analysis on 3min chart (HH/HL or LH/LL)
- **ytc-strength-weakness** - Momentum and pullback analysis

#### Active Trading Phase (4 agents)
- **ytc-setup-scanner** - Scans for valid trade setups (pullback, LWP/HWP)
- **ytc-entry-execution** - Executes entries when triggers hit
- **ytc-trade-management** - Manages stops, breakeven, partials, trailing
- **ytc-exit-execution** - Executes all types of exits

#### Support Agents (3 agents)
- **ytc-monitoring** - Real-time system and position monitoring
- **ytc-contingency** - Emergency handling and protective actions
- **ytc-logging-audit** - Complete audit trail logging

#### Post-Market Phase (4 agents)
- **ytc-session-review** - Trade-by-trade review and grading
- **ytc-performance-analytics** - Metrics (win rate, expectancy, Sharpe)
- **ytc-learning-optimization** - Pattern recognition and lessons
- **ytc-next-session-prep** - Goals, checklist, trading plan

## How to Use the Subagents

### Method 1: Direct Invocation via Task Tool

```python
# Example: Start a complete trading session
use Task tool with:
  subagent_type: "ytc-master-orchestrator"
  prompt: "Start YTC trading session for ETH/USD on binance_perpetual. Account balance: $100,000. Session duration: 3 hours."
```

### Method 2: Sequential Agent Invocation

```python
# Pre-Market Phase
1. Task(subagent_type="ytc-system-init", prompt="Initialize YTC system for ETH-USDT on binance_perpetual")
2. Task(subagent_type="ytc-risk-management", prompt="Calculate risk parameters for $100k account")
3. Task(subagent_type="ytc-market-structure", prompt="Analyze market structure on ETH-USDT 30min chart")
4. Task(subagent_type="ytc-economic-calendar", prompt="Check economic calendar and set restrictions")
5. Task(subagent_type="ytc-trend-definition", prompt="Define trend on ETH-USDT 3min chart")
6. Task(subagent_type="ytc-strength-weakness", prompt="Analyze strength and identify entry zones")

# Active Trading Phase (Loop)
7. Task(subagent_type="ytc-monitoring", prompt="Monitor system health and positions")
8. Task(subagent_type="ytc-setup-scanner", prompt="Scan for valid trade setups")
9. Task(subagent_type="ytc-entry-execution", prompt="Monitor setup triggers and execute entries")
10. Task(subagent_type="ytc-trade-management", prompt="Manage active positions")
11. Task(subagent_type="ytc-exit-execution", prompt="Execute exits when triggered")

# Post-Market Phase
12. Task(subagent_type="ytc-session-review", prompt="Review all trades from session")
13. Task(subagent_type="ytc-performance-analytics", prompt="Calculate performance metrics")
14. Task(subagent_type="ytc-learning-optimization", prompt="Extract lessons and optimization suggestions")
15. Task(subagent_type="ytc-next-session-prep", prompt="Prepare for next trading session")
```

## MCP_DOCKER Tools Available

Each subagent has access to these Hummingbot MCP tools:

### Portfolio & Market Data
- `get_portfolio_overview()` - Balances, positions, orders
- `get_candles()` - OHLC data for technical analysis
- `get_prices()` - Current price quotes
- `get_order_book()` - Market depth
- `get_funding_rate()` - Perpetual funding rates

### Trading Operations
- `place_order()` - Execute trades
- `manage_bot_execution()` - Start/stop bots
- `deploy_bot_with_controllers()` - Deploy strategies

### Risk & Configuration
- `set_account_position_mode_and_leverage()` - Configure account
- `configure_api_servers()` - Hummingbot connection
- `setup_connector()` - Exchange connector setup
- `search_history()` - Historical trade data

### Gateway Management
- `manage_gateway_container()` - Gateway lifecycle
- `manage_gateway_swaps()` - DEX swap operations
- `manage_gateway_clmm_positions()` - Liquidity positions

## Example Workflow: Complete Trading Session

```markdown
User: "Run a YTC trading session for ETH-USDT on binance_perpetual"

Claude: I'll orchestrate a complete YTC trading session. Let me start...

### Step 1: Invoke Master Orchestrator
Task(
  subagent_type="ytc-master-orchestrator",
  prompt="Start YTC trading session with the following parameters:
  - Instrument: ETH-USDT
  - Connector: binance_perpetual
  - Account: master_account
  - Initial Balance: $100,000
  - Risk per trade: 1%
  - Session loss limit: -3%
  - Max positions: 3
  - Session duration: 3 hours

  Execute complete workflow from pre-market through post-market phases."
)

### Master Orchestrator Will:
1. **Pre-Market** (15-20 minutes)
   - System initialization and health checks
   - Risk calculation and account setup
   - Market structure analysis (30min chart)
   - Economic calendar review
   - Trend definition (3min chart)
   - Strength/weakness analysis

2. **Active Trading** (2-3 hours, loop every 1-3 minutes)
   - Monitor system health
   - Scan for trade setups
   - Execute entries when triggers hit
   - Manage active positions (breakeven, partials, trailing)
   - Execute exits (stops, targets, time)
   - Continuous risk monitoring

3. **Post-Market** (10-15 minutes)
   - Session review and trade grading
   - Performance analytics
   - Learning and optimization
   - Next session preparation

### Expected Output:
Complete session report with:
- All trades executed with P&L
- Performance metrics (win rate, expectancy, R-multiples)
- Lessons learned
- Next session plan
```

## YTC Methodology Compliance

All subagents strictly follow YTC principles:

### Risk Management (Enforced by ytc-risk-management)
- ✅ 1% risk per trade
- ✅ 3% maximum session loss (auto-stop)
- ✅ Maximum 3 simultaneous positions
- ✅ Position sizing formula: `(Account × 0.01) / (Entry - Stop)`

### Multi-Timeframe Analysis
- ✅ **30min (HTF)**: Market structure, support/resistance (ytc-market-structure)
- ✅ **3min (TF)**: Trend definition, HH/HL or LH/LL (ytc-trend-definition)
- ✅ **1min (LTF)**: Entry timing and execution (ytc-entry-execution)

### Trade Management (Enforced by ytc-trade-management)
- ✅ Move stop to breakeven at +1R
- ✅ Take 50% profit at Target 1
- ✅ Trail stop on remaining 50%
- ✅ Time-based exits (max 2-4 hours)

### Setup Types (Identified by ytc-setup-scanner)
- ✅ Pullback to Structure
- ✅ Lower Weak Point (LWP) / Higher Weak Point (HWP)
- ✅ 3-Swing Trap Patterns
- ✅ Fibonacci entry zones (50%, 61.8%)

## Configuration

### Environment Setup
Ensure Hummingbot API is accessible:
```bash
# Check API servers
use: configure_api_servers()

# Setup connector if needed
use: setup_connector(connector="binance_perpetual", credentials={...})
```

### Account Configuration
```bash
# Set position mode and leverage (for perpetuals)
use: set_account_position_mode_and_leverage(
  account_name="master_account",
  connector_name="binance_perpetual",
  trading_pair="ETH-USDT",
  position_mode="HEDGE",
  leverage=5
)
```

## Safety Features

### Emergency Protocols (ytc-contingency)
- **Session Loss Limit**: Auto-stop at -3% P&L
- **Platform Failure**: Attempt to flatten positions, alert user
- **Multiple Stop Losses**: Pause after 3 consecutive losses
- **Abnormal Volatility**: Tighten stops or exit

### Continuous Monitoring (ytc-monitoring)
- Real-time P&L tracking
- Position health checks
- Stop loss verification
- System connectivity monitoring

### Complete Audit Trail (ytc-logging-audit)
- All decisions logged with timestamps
- Complete trade lifecycle records
- Risk calculations documented
- Immutable audit trail

## Success Criteria

A successful YTC session should achieve:
- ✅ All pre-market checks pass
- ✅ No trading until trend confirmed
- ✅ Only high-quality setups (score ≥7)
- ✅ All stops moved to breakeven at +1R
- ✅ Partials taken at targets
- ✅ Session stopped if -3% reached
- ✅ Complete post-market review
- ✅ Lessons extracted for improvement

## Troubleshooting

### Issue: Agent not responding
**Solution:** Check if agent file exists in `~/.claude/agents/`
```bash
ls ~/.claude/agents/ytc-*.md
```

### Issue: MCP tools not available
**Solution:** Verify MCP_DOCKER server is running
```bash
# Check available MCP tools
# Look for mcp__MCP_DOCKER__* tools
```

### Issue: Hummingbot connection failed
**Solution:** Configure API servers
```python
Task(subagent_type="ytc-system-init",
     prompt="Check Hummingbot connectivity and diagnose issues")
```

### Issue: Risk limits not enforced
**Solution:** Verify ytc-risk-management runs before entries
```python
Task(subagent_type="ytc-risk-management",
     prompt="Validate all risk parameters and enforce limits")
```

## Best Practices

1. **Always start with ytc-master-orchestrator** for complete sessions
2. **Run pre-market phase completely** before active trading
3. **Monitor continuously** during active trading phase
4. **Complete post-market review** even for losing sessions
5. **Learn from every session** - use ytc-learning-optimization
6. **Prepare for next session** - use ytc-next-session-prep

## Integration with Existing System

The old Python agents in `agents/*.py` can coexist with these subagents:
- **Old system**: LangGraph workflow, direct HummingbotGatewayClient calls
- **New system**: Claude Code subagents, MCP_DOCKER tools

**Migration Path:**
1. Test individual subagents independently
2. Compare outputs with old system
3. Gradually migrate to full subagent workflow
4. Eventually deprecate old Python agents

## Version History

- **v1.0.0** (2025-11-17): Initial conversion of 18 YTC agents to Anthropic subagents with MCP_DOCKER integration

---

**Remember:** The YTC system is designed to enforce strict discipline. Trust the process, follow the rules, and let the edge play out over time.

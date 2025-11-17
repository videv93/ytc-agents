# YTC Subagent Workflow - Example Usage

## Example 1: Complete Trading Session (Orchestrated)

### User Request
```
Start a YTC trading session for ETH/USD on binance_perpetual
```

### Claude Response
```python
# Using the master orchestrator for complete automation
use Task tool:
  subagent_type: "ytc-master-orchestrator"
  description: "Start YTC ETH/USD session"
  prompt: """
  Start a complete YTC trading session with these parameters:

  Instrument: ETH-USDT
  Connector: binance_perpetual
  Account: master_account
  Initial Balance: $100,000
  Session Duration: 3 hours

  Execute all phases:
  1. Pre-market: system init, risk calc, structure, calendar, trend, strength
  2. Active trading: continuous monitoring, setup scanning, entry/exit execution
  3. Post-market: review, analytics, learning, next session prep

  Enforce all YTC rules:
  - 1% risk per trade
  - 3% session loss limit
  - Max 3 simultaneous positions
  - Breakeven at +1R
  - Partials at T1
  """
```

### Expected Output from Orchestrator
```json
{
  "session_summary": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "phases_completed": ["pre_market", "active_trading", "post_market"],
    "duration_hours": 3.2,
    "trades_executed": 4,
    "final_pnl_usd": 1234.50,
    "final_pnl_pct": 1.23,
    "grade": "A-"
  },
  "phase_results": {
    "pre_market": {
      "system_ready": true,
      "trend_identified": "uptrend",
      "key_support": 2460.00,
      "key_resistance": 2500.00
    },
    "active_trading": {
      "setups_scanned": 8,
      "setups_taken": 4,
      "avg_setup_quality": 8.2,
      "winners": 3,
      "losers": 1
    },
    "post_market": {
      "lessons_learned": 5,
      "optimizations_suggested": 3,
      "next_session_prepared": true
    }
  }
}
```

---

## Example 2: Manual Step-by-Step Execution

### Pre-Market Phase

#### Step 1: System Initialization
```python
use Task tool:
  subagent_type: "ytc-system-init"
  prompt: "Initialize YTC system for ETH-USDT on binance_perpetual. Verify connectivity, load instrument specs, check account balance."

# Output: System ready, balance: $100k, latency: 45ms
```

#### Step 2: Risk Management
```python
use Task tool:
  subagent_type: "ytc-risk-management"
  prompt: "Calculate risk parameters for $100,000 account. Set position mode to HEDGE, leverage 5x on binance_perpetual for ETH-USDT."

# Output: Risk per trade: $1,000 (1%), Session stop: $97,000 (-3%)
```

#### Step 3: Market Structure Analysis
```python
use Task tool:
  subagent_type: "ytc-market-structure"
  prompt: "Analyze market structure on ETH-USDT 30min chart. Identify support/resistance zones, swing highs/lows. Fetch 7 days of 30min candles."

# Output: Support at 2460, 2480 | Resistance at 2500, 2520
```

#### Step 4: Economic Calendar
```python
use Task tool:
  subagent_type: "ytc-economic-calendar"
  prompt: "Check economic calendar for today. Any high-impact news events? Set trading restrictions if needed."

# Output: No major news, trading allowed
```

#### Step 5: Trend Definition
```python
use Task tool:
  subagent_type: "ytc-trend-definition"
  prompt: "Define trend on ETH-USDT 3min chart. Identify HH/HL or LH/LL pattern. Fetch last 2 hours of 3min candles."

# Output: Uptrend confirmed (HH/HL pattern), trade direction: LONG only
```

#### Step 6: Strength/Weakness Analysis
```python
use Task tool:
  subagent_type: "ytc-strength-weakness"
  prompt: "Analyze trend strength and identify entry zones. Calculate Fibonacci levels, assess pullback quality."

# Output: Strong trend, entry zone at 2485 (50% Fib), quality: excellent
```

---

### Active Trading Phase (Loop)

#### Cycle 1: Scan and Enter
```python
# Monitor
use Task tool:
  subagent_type: "ytc-monitoring"
  prompt: "Check system health, positions, session P&L"

# Scan for setups
use Task tool:
  subagent_type: "ytc-setup-scanner"
  prompt: "Scan for valid trade setups. Current price: 2485. Look for pullback to structure, LWP patterns."

# Output: Setup found: Pullback to 2485 support, quality score: 8/10

# Execute entry
use Task tool:
  subagent_type: "ytc-entry-execution"
  prompt: "Setup 'pullback_to_structure' triggered at 2487. Validate all conditions and execute entry if valid. Position size: calculate for 1% risk with stop at 2478."

# Output: Order filled - Long 0.42 ETH @ 2486.50, stop @ 2478
```

#### Cycle 2: Manage Position
```python
# Manage trade
use Task tool:
  subagent_type: "ytc-trade-management"
  prompt: "Manage active LONG position. Entry: 2486.50, Current: 2495.00, Stop: 2478. Check for breakeven move (+1R), partial exit at T1, trailing stop."

# Output: Moved stop to breakeven (2486.50) - position at +1R

# Continue management
use Task tool:
  subagent_type: "ytc-trade-management"
  prompt: "Position now at 2500. Check for partial exit at T1."

# Output: Partial exit - Closed 50% (0.21 ETH) @ 2500, locked $220 profit
```

#### Cycle 3: Exit Position
```python
# Monitor for exit
use Task tool:
  subagent_type: "ytc-exit-execution"
  prompt: "Monitor position for exit triggers. Remaining: 0.21 ETH, Current: 2510, Trailing stop: 2495, T2: 2510"

# Output: Target 2 hit - Closed remaining 0.21 ETH @ 2510, total P&L: $494.50
```

---

### Post-Market Phase

#### Review Session
```python
use Task tool:
  subagent_type: "ytc-session-review"
  prompt: "Review all trades from today's session. Analyze each trade, grade decisions, identify lessons."

# Output: 4 trades, 3 wins, 1 loss. Win rate: 75%. Grade: A-
```

#### Performance Analytics
```python
use Task tool:
  subagent_type: "ytc-performance-analytics"
  prompt: "Calculate performance metrics for last 30 days. Include win rate, expectancy, Sharpe ratio, max drawdown."

# Output: Win rate: 62%, Expectancy: +0.78R, Max DD: -4.2%
```

#### Learning & Optimization
```python
use Task tool:
  subagent_type: "ytc-learning-optimization"
  prompt: "Analyze trading patterns and extract lessons. Identify best/worst setups, common mistakes, optimization opportunities."

# Output: Best setup: pullback_to_structure (71% win rate), Lesson: Wait for full 3-bar rejection
```

#### Next Session Prep
```python
use Task tool:
  subagent_type: "ytc-next-session-prep"
  prompt: "Prepare for tomorrow's session. Set goals, create checklist, identify key levels, plan scenarios."

# Output: Goal: 3 trades, +2R minimum, Focus: pullback_to_structure only
```

---

## Example 3: Emergency Scenario

### Session Loss Limit Approaching
```python
# Monitoring detects issue
use Task tool:
  subagent_type: "ytc-monitoring"
  prompt: "Check session P&L and risk status"

# Output: WARNING - Session P&L: -2.8% (approaching -3% limit)

# Contingency triggered
use Task tool:
  subagent_type: "ytc-contingency"
  prompt: "Session P&L at -2.8%. Check if emergency stop required. If approaching -3%, prepare to close all positions."

# Output: CRITICAL - Session P&L hit -3.01%
# Actions: Closed 2 open positions, stopped trading, generated emergency report

# Session review for emergency
use Task tool:
  subagent_type: "ytc-session-review"
  prompt: "Emergency stop triggered. Review session trades, identify what went wrong."

# Output: 5 trades, 2 wins, 3 losses. Issue: Traded during choppy market without clear trend. Lesson: Only trade strong trends.
```

---

## Example 4: Single Agent Testing

### Test Market Structure Agent Alone
```python
use Task tool:
  subagent_type: "ytc-market-structure"
  prompt: """
  Analyze ETH-USDT market structure on binance_perpetual.

  Tasks:
  1. Fetch 7 days of 30min candles
  2. Identify swing highs and swing lows (lookback=2)
  3. Group into support/resistance zones
  4. Determine current price context
  5. Provide visual text representation

  Current instrument: ETH-USDT
  Connector: binance_perpetual
  """

# Output: Detailed structure analysis with zones, swings, and context
```

### Test Risk Management Agent Alone
```python
use Task tool:
  subagent_type: "ytc-risk-management"
  prompt: """
  Calculate position size for the following trade:

  Account Balance: $100,000
  Entry Price: $2,500
  Stop Loss: $2,480
  Risk per trade: 1%

  Also calculate:
  - Session stop loss level (-3%)
  - Verify position count limit (currently 2 open)
  - Check if new trade allowed
  """

# Output: Position size: 50 ETH, Session stop: $97,000, New trade: ALLOWED (2/3 positions)
```

---

## Tips for Effective Usage

### 1. Always Provide Context
```python
# GOOD
prompt: "Analyze ETH-USDT structure on binance_perpetual. Current price: 2485. Fetch 7 days of 30min data."

# BAD
prompt: "Analyze structure"
```

### 2. Specify Data Requirements
```python
# GOOD
prompt: "Get 3min candles for last 2 hours for trend analysis"

# BAD
prompt: "Get candles"
```

### 3. Include Current State
```python
# GOOD
prompt: "Manage position. Entry: 2486.50, Current: 2495, Stop: 2478, Size: 0.42 ETH"

# BAD
prompt: "Manage my position"
```

### 4. Request Specific Actions
```python
# GOOD
prompt: "Check if setup 'pullback_to_structure' triggered at 2487. If yes, validate and execute entry."

# BAD
prompt: "Should I enter?"
```

---

## Debugging Workflows

### Check Agent Status
```bash
# List all YTC agents
ls ~/.claude/agents/ytc-*.md

# Should show 18 agents
```

### Verify MCP Tools
```python
# Check if MCP_DOCKER tools available
# Look for these functions:
# - get_portfolio_overview
# - get_candles
# - place_order
# - etc.
```

### Test Individual Components
```python
# Test system connectivity
use Task tool:
  subagent_type: "ytc-system-init"
  prompt: "Run all connectivity checks and report status"

# Test risk calculation
use Task tool:
  subagent_type: "ytc-risk-management"
  prompt: "Calculate position size for $100k account, entry 2500, stop 2480"
```

---

**Remember:** The subagent system is designed to work together. The master orchestrator handles coordination, or you can invoke agents individually for specific tasks.

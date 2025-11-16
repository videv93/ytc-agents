# YTC Agent System - Quick Reference Guide

## Complete Agent List

| ID | Agent Name | Phase | Priority | Purpose |
|----|------------|-------|----------|---------|
| 00 | Master Orchestrator | All | Critical | Session coordination & workflow |
| 01 | System Initialization | Pre-Market | Critical | Platform connectivity |
| 02 | Risk Management | Pre-Market + Live | Critical | Position sizing & limits |
| 03 | Market Structure | Pre-Market | High | Higher TF S/R zones |
| 04 | Economic Calendar | Pre-Market + Live | High | News filtering |
| 05 | Trend Definition | Session Open + Live | Critical | Trading TF trend |
| 06 | Strength & Weakness | Session Open + Live | High | Momentum analysis |
| 07 | Setup Scanner | Active Trading | Critical | Pattern detection |
| 08 | Entry Execution | Active Trading | Critical | Trade entry |
| 09 | Trade Management | Active Trading | Critical | Position management |
| 10 | Exit Execution | Active Trading | Critical | Trade exits |
| 11 | Real-Time Monitoring | All | High | Live monitoring |
| 12 | Session Review | Post-Market | High | Performance review |
| 13 | Performance Analytics | Post-Market | Medium | Statistics |
| 14 | Learning & Optimization | Post-Market | Medium | Parameter tuning |
| 15 | Next Session Prep | Post-Market | Low | Goal setting |
| 16 | Contingency Management | All | Critical | Emergency handling |
| 17 | Logging & Audit | All | High | Audit trail |

## Execution Flow

```
PRE-MARKET (1-2 hours before open)
├── 00: Initialize Session
├── 01: Platform Setup
├── 02: Risk Calculation  
├── 03: Structure Analysis (30min)
└── 04: News Calendar

SESSION OPEN (First 15-30 min)
├── 05: Define Trend (3min)
└── 06: Analyze Strength

ACTIVE TRADING (Main session)
├── 07: Scan for Setups
├── 08: Execute Entry
├── 09: Manage Position
├── 10: Execute Exit
├── 11: Monitor (continuous)
├── 16: Watch for Emergencies (continuous)
└── 17: Log Everything (continuous)

POST-MARKET (After close)
├── 12: Review Session
├── 13: Calculate Stats
├── 14: Optimize Parameters
└── 15: Prepare Next Session
```

## Key Skills by Agent

### 00 - Master Orchestrator
- Workflow state machine
- Risk guardian
- Agent orchestration
- Emergency protocol handler

### 01 - System Initialization
- Connection validator
- System configuration manager
- Clock synchronization
- Instrument loader

### 02 - Risk Management  
- Position size calculator (YTC formula)
- Session risk monitor
- Correlation risk analyzer
- Trade request validator

### 03 - Market Structure
- Swing point detection (30min)
- S/R zone calculation
- Structure classifier
- Zone strength scoring

### 04 - Economic Calendar
- News API integration
- Impact classifier
- Restriction manager
- Alert scheduler

### 05 - Trend Definition
- Pivot detector (3min)
- Trend classifier (HH/HL, LH/LL)
- Leading swing tracker
- Structure integrity monitor

### 06 - Strength & Weakness
- Momentum analyzer
- Projection comparator
- Depth calculator
- Multi-component scorer

### 07 - Setup Scanner
- Pullback detector
- 3-swing trap identifier
- Fibonacci calculator
- Setup quality scorer

### 08 - Entry Execution
- LWP identifier
- Fibonacci entry monitor
- Dynamic level updater
- Order manager

### 09 - Trade Management
- Trailing stop logic
- Partial exit manager
- Breakeven calculator
- Time-based exit monitor

### 10 - Exit Execution
- Multi-exit handler (target/stop/time/signal)
- Fill verifier
- Position flattener
- Trade recorder

### 11 - Real-Time Monitoring
- Anomaly detector
- Health checker
- Progress tracker
- Alert generator

### 12 - Session Review
- Hindsight analyzer
- Trade quality assessor
- Lesson extractor
- Environment classifier

### 13 - Performance Analytics
- Statistics calculator
- Journal updater
- Trend analyzer
- Performance tracker

### 14 - Learning & Optimization
- Parameter optimizer
- Edge case documenter
- Pattern recognizer
- Recommendation generator

### 15 - Next Session Prep
- Goal setter
- Focus identifier
- Calendar updater
- Checklist generator

### 16 - Contingency Management
- Emergency detector
- Shutdown executor
- Recovery manager
- Failover handler

### 17 - Logging & Audit
- Decision logger
- Trade recorder
- Event tracker
- Audit trail maintainer

## Hummingbot API Methods Used

### Core Methods
```python
# Connection & Status
hummingbot.gateway.get_status()
hummingbot.gateway.ping()
hummingbot.status()

# Market Data
hummingbot.get_price_history(connector, pair, interval, limit)
hummingbot.get_mid_price(connector, pair)
hummingbot.get_order_book(connector, pair)

# Account Management
hummingbot.get_balance(connector, asset)
hummingbot.get_balances()

# Order Management
hummingbot.create_order(connector, pair, side, amount, type, price)
hummingbot.cancel_order(order_id)
hummingbot.cancel_all_orders()
hummingbot.get_order(order_id)
hummingbot.get_open_orders()

# Position Management
hummingbot.get_positions()

# Performance
hummingbot.get_trades(days)
hummingbot.get_performance_metrics()
```

## Critical YTC Rules Implemented

### Risk Management
- ✅ 1% risk per trade (exact calculation)
- ✅ 3% maximum session loss
- ✅ Maximum 3 simultaneous positions
- ✅ 3% total exposure limit
- ✅ Correlation detection & prevention

### Trend Analysis
- ✅ Higher highs + higher lows = uptrend
- ✅ Lower highs + lower lows = downtrend
- ✅ Structure break ≠ trend reversal
- ✅ Leading swing violation = reversal
- ✅ Distinguish weakening from reversing

### Setup Recognition
- ✅ Pullback to structure
- ✅ 3-swing trap pattern
- ✅ Fibonacci retracements (50%, 61.8%)
- ✅ Setup quality scoring
- ✅ Confluence checking

### Trade Management
- ✅ Initial stop beyond structure
- ✅ Trailing stops at pivots
- ✅ Move to breakeven at +1R
- ✅ Partial exits at T1
- ✅ Let winners run (T2)

### Review Process
- ✅ Compare to hindsight-perfect
- ✅ Identify optimal entry/exit
- ✅ Calculate execution efficiency
- ✅ Extract lessons learned
- ✅ Set process goals

## Inter-Agent Communication

### Message Queue (Redis)
```python
# Task submission
redis.lpush('agent_tasks', json.dumps({
    'task_id': uuid,
    'agent': 'risk_management',
    'data': {...}
}))

# Result retrieval
result = redis.blpop('agent_results', timeout=60)
```

### Shared State (PostgreSQL)
```python
# Update session state
db.execute("""
    UPDATE trading.sessions 
    SET session_pnl = %s, trades_count = %s
    WHERE session_id = %s
""", (pnl, count, session_id))
```

## Configuration Files

### session_config.yaml
```yaml
market: forex
instrument: GBP/USD
timeframes:
  higher: 30min
  trading: 3min
  lower: 1min
session:
  start_time: "09:30:00"
  duration_hours: 3
  timezone: America/New_York
```

### risk_config.yaml
```yaml
risk_per_trade_pct: 1.0
max_session_risk_pct: 3.0
max_positions: 3
max_total_exposure_pct: 3.0
consecutive_loss_limit: 5
correlation_threshold: 0.7
```

### agent_config.yaml
```yaml
agents:
  enabled:
    - all
  
  system_init:
    connection_timeout: 10
    max_retries: 3
  
  risk_management:
    strict_mode: true
    allow_partial_contracts: false
  
  setup_scanner:
    min_score: 70
    enabled_patterns:
      - pullback
      - 3_swing_trap
```

## Deployment Checklist

### Pre-Deployment
- [ ] All agents tested
- [ ] Database schema created
- [ ] Environment variables set
- [ ] Hummingbot configured
- [ ] Broker API keys loaded
- [ ] Risk limits validated

### Deployment
- [ ] Start PostgreSQL
- [ ] Start Redis
- [ ] Start Hummingbot Gateway
- [ ] Deploy YTC system
- [ ] Verify all connections
- [ ] Run health checks

### Post-Deployment
- [ ] Monitor first session
- [ ] Verify trade execution
- [ ] Check audit logs
- [ ] Review performance
- [ ] Validate risk enforcement

## Troubleshooting

### Common Issues

**Connection Lost**
- Check Hummingbot gateway status
- Verify broker API connectivity
- Review network logs
- Trigger failover if needed

**Trade Not Executing**
- Check risk validation logs
- Verify position size calculation
- Review setup scoring
- Check margin availability

**Agent Timeout**
- Increase timeout settings
- Check agent dependencies
- Review execution logs
- Verify API rate limits

**Incorrect Position Size**
- Verify instrument specs loaded
- Check risk % calculation
- Review stop distance
- Validate tick size/value

## Support Resources

### Documentation
- Agent specifications: `*.md` files
- Implementation guide: `IMPLEMENTATION_GUIDE.md`
- Architecture: `ARCHITECTURE.md`
- README: `README.md`

### YTC Source Material
- Volume 1: Introduction & Basics
- Volume 2: Price Action
- Volume 3: Trading Process
- Volume 4: Business Management
- Volume 5: Trader Development  
- Volume 6: Strategy Summary

### API Documentation
- Anthropic: https://docs.anthropic.com
- Hummingbot: https://docs.hummingbot.io

---

**Quick Start**: See IMPLEMENTATION_GUIDE.md  
**Questions**: Review individual agent .md files  
**Issues**: Check troubleshooting section above

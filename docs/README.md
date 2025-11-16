# YTC Automated Trading System - Agent Architecture

## Overview

This is a complete multi-agent system for automating the YTC (Your Trading Coach) Price Action methodology created by Lance Beggs. The system uses Anthropic's Claude with Hummingbot API integration to execute a comprehensive trading workflow from pre-market analysis through post-market review.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   MASTER ORCHESTRATOR                        │
│            (Session Lifecycle & Coordination)                │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼──────┐         ┌────────▼────────┐
│  PRE-MARKET  │         │  SUPPORT AGENTS │
│    AGENTS    │         │  (Always Active) │
│              │         │                  │
│ 01. System   │         │ 11. Real-Time   │
│     Init     │         │     Monitoring  │
│ 02. Risk     │         │ 16. Contingency │
│     Mgmt     │         │ 17. Logging     │
│ 03. Market   │         │                  │
│     Structure│         └─────────────────┘
│ 04. Economic │
│     Calendar │
└──────┬───────┘
       │
┌──────▼────────┐
│ SESSION OPEN  │
│    AGENTS     │
│               │
│ 05. Trend     │
│     Definition│
│ 06. Strength  │
│     & Weakness│
└──────┬────────┘
       │
┌──────▼────────┐
│ ACTIVE TRADE  │
│    AGENTS     │
│               │
│ 07. Setup     │
│     Scanner   │
│ 08. Entry     │
│     Execution │
│ 09. Trade     │
│     Management│
│ 10. Exit      │
│     Execution │
└──────┬────────┘
       │
┌──────▼────────┐
│  POST-MARKET  │
│    AGENTS     │
│               │
│ 12. Session   │
│     Review    │
│ 13. Performance│
│     Analytics │
│ 14. Learning  │
│     & Optim   │
│ 15. Next      │
│     Session   │
└───────────────┘
```

## Agent Inventory

### Critical Path Agents (17 Total)

1. **00_MASTER_ORCHESTRATOR** - Central coordinator
2. **01_SYSTEM_INITIALIZATION** - Platform connectivity
3. **02_RISK_MANAGEMENT** - Position sizing & limits
4. **03_MARKET_STRUCTURE** - Higher timeframe S/R
5. **04_ECONOMIC_CALENDAR** - News filtering
6. **05_TREND_DEFINITION** - Trading timeframe trend
7. **06_STRENGTH_WEAKNESS** - Momentum analysis
8. **07_SETUP_SCANNER** - Pattern recognition
9. **08_ENTRY_EXECUTION** - Trade entry
10. **09_TRADE_MANAGEMENT** - Position management
11. **10_EXIT_EXECUTION** - Trade exits
12. **11_REAL_TIME_MONITORING** - Continuous monitoring
13. **12_SESSION_REVIEW** - Post-session analysis
14. **13_PERFORMANCE_ANALYTICS** - Statistics tracking
15. **14_LEARNING_OPTIMIZATION** - Parameter tuning
16. **15_NEXT_SESSION_PREP** - Goal setting
17. **16_CONTINGENCY_MANAGEMENT** - Emergency handling
18. **17_LOGGING_AUDIT** - Audit trail

## Key Features

### YTC Methodology Implementation

- ✅ **Multiple Timeframe Analysis** (30min structure / 3min trading / 1min entry)
- ✅ **Precise Risk Management** (1% per trade, 3% session max)
- ✅ **Swing-Based Trend Analysis** (HH/HL for uptrends, LH/LL for downtrends)
- ✅ **Strength & Weakness Scoring** (Momentum + Projection + Depth)
- ✅ **Setup Recognition** (Pullbacks, 3-Swing Traps, Continuation)
- ✅ **Fibonacci Retracements** (50%, 61.8% entry zones)
- ✅ **Trade Management** (Pivot-based trailing stops, partial exits)
- ✅ **Session Review Process** (Compare to hindsight-perfect execution)

### Technical Features

- 🔧 **Hummingbot Integration** - Direct API connectivity
- 🤖 **Anthropic Claude** - Intelligent decision making
- 📊 **Real-Time Monitoring** - Continuous market surveillance
- 🛡️ **Risk Controls** - Multiple layers of protection
- 📝 **Complete Audit Trail** - Every decision logged
- ⚡ **Emergency Protocols** - Automatic failure handling
- 📈 **Performance Analytics** - Comprehensive statistics
- 🎯 **Correlation Detection** - Multi-position risk management

## Technology Stack

### Required Components

1. **Anthropic Claude API** - Agent intelligence
2. **Hummingbot Framework** - Trading platform
3. **Python 3.8+** - Core language
4. **PostgreSQL** - State management database
5. **Redis** - Message queue
6. **WebSocket** - Real-time data feeds

### Optional Components

- **Prometheus/Grafana** - Monitoring dashboards
- **Docker** - Containerization
- **Kubernetes** - Orchestration
- **Jupyter** - Analysis notebooks

## File Structure

```
ytc_agents/
├── README.md                          # This file
├── IMPLEMENTATION_GUIDE.md            # Setup instructions
├── ARCHITECTURE.md                    # Detailed architecture
├── HUMMINGBOT_INTEGRATION.md         # Hummingbot specifics
├── 00_MASTER_ORCHESTRATOR.md         # Central coordinator
├── 01_SYSTEM_INITIALIZATION.md       # Platform setup
├── 02_RISK_MANAGEMENT.md             # Risk controls
├── 03_MARKET_STRUCTURE.md            # Higher TF analysis
├── 04_ECONOMIC_CALENDAR.md           # News filtering
├── 05_TREND_DEFINITION.md            # Trend analysis
├── 06_STRENGTH_WEAKNESS.md           # Momentum scoring
├── 07_SETUP_SCANNER.md               # Pattern detection
├── 08_ENTRY_EXECUTION.md             # Entry orders
├── 09_TRADE_MANAGEMENT.md            # Position mgmt
├── 10_EXIT_EXECUTION.md              # Exit orders
├── 11_REAL_TIME_MONITORING.md        # Live monitoring
├── 12_SESSION_REVIEW.md              # Post-session
├── 13_PERFORMANCE_ANALYTICS.md       # Statistics
├── 14_LEARNING_OPTIMIZATION.md       # Tuning
├── 15_NEXT_SESSION_PREP.md           # Planning
├── 16_CONTINGENCY_MANAGEMENT.md      # Emergencies
└── 17_LOGGING_AUDIT.md               # Audit trail
```

## Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install anthropic hummingbot redis psycopg2

# Setup Hummingbot
# Follow: https://docs.hummingbot.io/

# Configure environment
export ANTHROPIC_API_KEY="your_key_here"
export HUMMINGBOT_GATEWAY_URL="http://localhost:15888"
```

### Basic Usage

```python
from ytc_orchestrator import MasterOrchestrator

# Initialize system
orchestrator = MasterOrchestrator(
    session_config={
        "market": "forex",
        "instrument": "GBP/USD",
        "session_duration_hours": 3
    }
)

# Start trading session
session_id = orchestrator.start_session()

# Monitor (blocking)
orchestrator.run()

# Or monitor non-blocking
while orchestrator.is_active():
    orchestrator.process_cycle()
    time.sleep(1)

# Generate report
report = orchestrator.end_session()
```

## Configuration

### Risk Parameters

```yaml
risk_config:
  risk_per_trade_pct: 1.0           # 1% per trade
  max_session_risk_pct: 3.0         # 3% max session loss
  max_positions: 3                   # Max simultaneous
  max_total_exposure_pct: 3.0       # Total exposure cap
  consecutive_loss_limit: 5          # Stop after 5 losses
```

### Timeframes

```yaml
timeframes:
  higher: "30min"    # Structure & S/R
  trading: "3min"    # Trend & Setups
  lower: "1min"      # Entry refinement
```

### Session Configuration

```yaml
session:
  start_time: "09:30:00"
  duration_hours: 3
  timezone: "America/New_York"
  enable_pre_market: false
  enable_post_market: false
```

## Risk Controls

### Multi-Layer Protection

1. **Pre-Trade Validation**
   - Position size calculation
   - Risk limit checks
   - Correlation analysis
   - Margin validation

2. **During Trade**
   - Real-time P&L monitoring
   - Session limit tracking
   - Structure break detection
   - Time-based exits

3. **Emergency Protocols**
   - Automatic position flattening
   - Connection loss handling
   - Platform failure recovery
   - Manual override capability

### Session Stop Loss

```
If session P&L <= -3%:
  1. Cancel all pending orders
  2. Close all positions
  3. Halt trading
  4. Generate emergency report
  5. Alert operator
```

## Performance Monitoring

### Real-Time Metrics

- Current P&L ($ and %)
- Risk utilization
- Win rate
- Average R-multiple
- Time in session
- Trades taken
- System health

### Post-Session Analytics

- Trade-by-trade review
- Setup type performance
- Entry/exit quality
- Optimal vs actual execution
- Lessons learned
- Improvement recommendations

## YTC Methodology Compliance

### Core Principles

✅ **Trade What You See** - Pure price action analysis  
✅ **Risk Management First** - Never exceed limits  
✅ **Quality Over Quantity** - Wait for A+ setups  
✅ **Trend Structure** - Trade with structure alignment  
✅ **Review & Improve** - Deliberate practice cycle  

### Procedures Manual

Each agent implements YTC's procedures manual:
- Pre-session checklist
- During-session workflow
- Post-session review
- Continuous improvement

## Testing

### Unit Tests

```bash
pytest tests/unit/
```

### Integration Tests

```bash
pytest tests/integration/
```

### Backtesting

```bash
python backtest.py --config config/test_config.yaml --start 2024-01-01 --end 2024-12-31
```

## Deployment

### Docker Deployment

```bash
docker-compose up -d
```

### Kubernetes Deployment

```bash
kubectl apply -f k8s/
```

## Monitoring & Alerts

### Prometheus Metrics

- Agent execution times
- Error rates
- Trade performance
- System health

### Alert Channels

- Email notifications
- Telegram bot
- Webhook integrations
- SMS (critical only)

## Security

- API keys encrypted at rest
- Secure credential storage
- Audit logging enabled
- Access control implemented
- Network isolation

## Compliance

- Complete audit trail
- Trade justification logging
- Decision reasoning captured
- Regulatory reporting ready
- Performance attribution

## Support

### Documentation

- See individual agent .md files
- Check IMPLEMENTATION_GUIDE.md
- Review ARCHITECTURE.md
- Read YTC volumes 1-6

### Community

- GitHub Issues
- Discord Channel
- Email Support

## Disclaimer

This system is for educational purposes. Trading involves substantial risk of loss. Past performance does not guarantee future results. Only trade with capital you can afford to lose.

The YTC methodology is the intellectual property of Lance Beggs (YourTradingCoach.com). This implementation is an independent interpretation and not endorsed by the original author.

## License

MIT License - See LICENSE file

## Version History

- v1.0.0 - Initial release with complete agent architecture
- Full YTC methodology implementation
- Hummingbot integration
- Complete documentation

## Credits

- **YTC Methodology**: Lance Beggs (YourTradingCoach.com)
- **Trading Platform**: Hummingbot Foundation
- **AI Framework**: Anthropic Claude
- **Implementation**: Vi (2025)

---

**Ready to automate your YTC trading? Start with IMPLEMENTATION_GUIDE.md**

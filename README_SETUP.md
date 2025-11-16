# YTC Trading System - Setup Guide

## Quick Start

### 1. Clone and Setup

```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

**Required configuration:**
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `POSTGRES_PASSWORD`: Secure password for PostgreSQL
- Other settings can use defaults for testing

### 3. Start Services

#### Option A: Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f ytc-system

# Stop services
docker-compose down
```

#### Option B: Local Development

```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Start Redis
sudo systemctl start redis

# Create database
psql -U postgres -c "CREATE DATABASE ytc_trading;"
psql -U postgres -c "CREATE USER ytc_trader WITH PASSWORD 'your_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ytc_trading TO ytc_trader;"

# Run the system
python main.py
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agents --cov=skills --cov=tools

# Run specific test file
pytest tests/unit/test_risk_management.py -v
```

## Project Structure

```
ytc-agents/
├── agents/              # All trading agents
│   ├── base.py         # Base agent class
│   ├── orchestrator.py # Master orchestrator
│   ├── system_init.py  # System initialization
│   └── risk_management.py
├── skills/             # Reusable skills
│   ├── pivot_detection.py
│   └── fibonacci.py
├── database/           # Database layer
│   ├── models.py       # SQLAlchemy models
│   └── connection.py   # Connection manager
├── config/             # Configuration files
│   ├── session_config.yaml
│   ├── risk_config.yaml
│   └── agent_config.yaml
├── tests/              # Test suite
│   ├── unit/
│   └── integration/
├── main.py             # Application entry point
├── requirements.txt    # Python dependencies
├── pyproject.toml      # Project configuration
└── docker-compose.yml  # Docker deployment
```

## Key Components

### Base Agent Framework
- **BaseAgent**: Abstract base class for all agents
- **TradingState**: Shared state across agents
- **LangGraph Integration**: Workflow orchestration

### Implemented Agents
1. **Master Orchestrator** - Coordinates all agents
2. **System Init** - Platform connectivity
3. **Risk Management** - Position sizing and limits

### Skills Library
- **Pivot Detection** - YTC swing point identification
- **Fibonacci** - Retracement and extension calculations

### Database
- **PostgreSQL** - Persistent storage
- **SQLAlchemy** - ORM layer
- **Schemas**: trading, analytics, audit

## Configuration

### Risk Settings
Edit `config/risk_config.yaml`:
```yaml
risk_per_trade_pct: 1.0
max_session_risk_pct: 3.0
max_positions: 3
```

### Session Settings
Edit `config/session_config.yaml`:
```yaml
market: crypto
instrument: ETH/USD
timeframes:
  higher: 30min
  trading: 3min
```

## Development Workflow

### Adding a New Agent

1. Create agent file in `agents/` directory:
```python
from agents.base import BaseAgent, TradingState

class MyNewAgent(BaseAgent):
    async def _execute_logic(self, state: TradingState):
        # Your agent logic here
        return {'status': 'success'}
```

2. Register in orchestrator (`agents/orchestrator.py`)

3. Add tests in `tests/unit/test_my_new_agent.py`

### Adding a New Skill

1. Create skill file in `skills/` directory
2. Add tests
3. Import in relevant agents

## Monitoring

### View Logs
```bash
# Docker
docker-compose logs -f ytc-system

# Local
tail -f logs/ytc_system.log
```

### Database Queries
```bash
# Connect to database
docker-compose exec postgres psql -U ytc_trader -d ytc_trading

# View sessions
SELECT * FROM trading.sessions ORDER BY start_time DESC LIMIT 10;

# View trades
SELECT * FROM trading.trades ORDER BY entry_time DESC LIMIT 10;
```

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
docker-compose exec postgres pg_isready
```

### API Key Issues
- Verify `ANTHROPIC_API_KEY` in `.env`
- Check API key has proper permissions
- Verify API quota not exceeded

### Agent Execution Issues
- Check logs for error messages
- Verify all required fields in state
- Run tests to isolate issues

## Next Steps

1. **Paper Trading**: Test with paper trading account
2. **Add More Agents**: Implement remaining 14 agents
3. **Backtesting**: Create backtesting framework
4. **Monitoring**: Add Grafana dashboards
5. **Optimization**: Tune parameters based on results

## Resources

- **YTC Methodology**: Read YTC Price Action Volumes 1-6
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Anthropic Docs**: https://docs.anthropic.com
- **Hummingbot Docs**: https://docs.hummingbot.io

## Support

For issues or questions:
1. Check the implementation guide in `docs/`
2. Review agent documentation
3. Run tests to verify setup
4. Check logs for errors

---

**Warning**: This is a trading system. Always test thoroughly with paper trading before using real capital. Never risk more than you can afford to lose.

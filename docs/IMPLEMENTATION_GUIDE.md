# YTC Automated Trading System - Implementation Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Hummingbot Configuration](#hummingbot-configuration)
4. [Agent Implementation](#agent-implementation)
5. [Database Setup](#database-setup)
6. [Testing & Validation](#testing--validation)
7. [Deployment](#deployment)
8. [Operational Guide](#operational-guide)

---

## Prerequisites

### Knowledge Requirements

- ✅ Understanding of YTC Price Action methodology (read volumes 1-6)
- ✅ Python programming experience (intermediate level)
- ✅ Trading platform experience (Hummingbot preferred)
- ✅ Basic understanding of APIs and webhooks
- ✅ Database concepts (PostgreSQL)
- ✅ Message queuing concepts (Redis)

### System Requirements

```yaml
Hardware:
  CPU: 4+ cores recommended
  RAM: 8GB minimum, 16GB recommended
  Storage: 50GB SSD
  Network: Stable internet connection (<50ms latency to broker)

Software:
  OS: Linux (Ubuntu 22.04 LTS recommended) or macOS
  Python: 3.10 or higher
  Docker: 20.10+ (optional but recommended)
  PostgreSQL: 14+
  Redis: 6.2+
```

### Account Requirements

- Anthropic API account with Claude access
- Hummingbot installation (Gateway mode)
- Broker account with API access
- Market data subscription
- Sufficient trading capital (minimum $10,000 recommended)

---

## Environment Setup

### Step 1: Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Redis
sudo apt install redis-server -y

# Install build tools
sudo apt install build-essential git -y
```

### Step 2: Create Project Structure

```bash
# Create project directory
mkdir -p ~/ytc-trading-system
cd ~/ytc-trading-system

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Create directory structure
mkdir -p {agents,config,logs,data,tests,skills}
```

### Step 3: Install Python Dependencies

```bash
# Create requirements.txt
cat > requirements.txt << 'EOF'
anthropic==0.18.1
hummingbot==1.25.0
redis==5.0.1
psycopg2-binary==2.9.9
pandas==2.1.4
numpy==1.26.3
python-dotenv==1.0.0
pyyaml==6.0.1
requests==2.31.0
websocket-client==1.7.0
asyncio==3.4.3
aiohttp==3.9.1
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.12.1
flake8==7.0.0
mypy==1.8.0
EOF

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Environment Variables

```bash
# Create .env file
cat > .env << 'EOF'
# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Hummingbot Configuration
HUMMINGBOT_GATEWAY_URL=http://localhost:15888
HUMMINGBOT_API_KEY=your_hummingbot_api_key

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ytc_trading
POSTGRES_USER=ytc_trader
POSTGRES_PASSWORD=your_secure_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Trading Configuration
TRADING_MARKET=forex
TRADING_INSTRUMENT=GBP/USD
SESSION_START_TIME=09:30:00
SESSION_DURATION_HOURS=3
TIMEZONE=America/New_York

# Risk Configuration
RISK_PER_TRADE_PCT=1.0
MAX_SESSION_RISK_PCT=3.0
MAX_POSITIONS=3

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/ytc_system.log
EOF

# Secure .env file
chmod 600 .env
```

---

## Hummingbot Configuration

### Step 1: Install Hummingbot

```bash
# Using Docker (Recommended)
docker pull hummingbot/hummingbot:latest

# Or install from source
git clone https://github.com/hummingbot/hummingbot.git
cd hummingbot
./install
```

### Step 2: Configure Hummingbot Gateway

```bash
# Start Hummingbot Gateway
cd ~/hummingbot-gateway
yarn start

# Or using Docker
docker run -d \
  --name hummingbot-gateway \
  -p 15888:15888 \
  -v $(pwd)/conf:/usr/src/app/conf \
  hummingbot/gateway:latest
```

### Step 3: Configure Connectors

```bash
# Access Hummingbot
docker exec -it hummingbot bash

# Inside Hummingbot, configure your exchange/broker
>>> connect [exchange_name]
>>> # Follow prompts to enter API keys

# Test connection
>>> balance
>>> ticker [trading_pair]
```

### Step 4: Verify API Access

```python
# Test script: test_hummingbot.py
import requests

gateway_url = "http://localhost:15888"

# Test gateway status
response = requests.get(f"{gateway_url}/")
print(f"Gateway Status: {response.json()}")

# Test connector
response = requests.get(f"{gateway_url}/connectors")
print(f"Connectors: {response.json()}")

# Test balance
response = requests.post(
    f"{gateway_url}/balance",
    json={"connector": "your_exchange", "chain": "ethereum"}
)
print(f"Balance: {response.json()}")
```

---

## Agent Implementation

### Step 1: Core Agent Framework

```python
# agents/base_agent.py
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging
from datetime import datetime

class BaseAgent(ABC):
    """Base class for all YTC trading agents"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self.logger = logging.getLogger(agent_id)
        self.state = {}
        
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method - must be implemented by each agent
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Dict containing agent output
        """
        pass
    
    def validate_input(self, input_data: Dict[str, Any], schema: Dict) -> bool:
        """Validates input against expected schema"""
        # Implementation
        return True
    
    def log_decision(self, decision_type: str, data: Dict[str, Any]):
        """Logs agent decision with context"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'agent_id': self.agent_id,
            'decision_type': decision_type,
            'data': data
        }
        self.logger.info(log_entry)
        
    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Standard error handling"""
        self.logger.error(f"Error in {self.agent_id}: {str(error)}")
        return {
            'status': 'error',
            'error': str(error),
            'agent_id': self.agent_id
        }
```

### Step 2: Implement Master Orchestrator

```python
# agents/master_orchestrator.py
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
import asyncio

class MasterOrchestrator(BaseAgent):
    """Central coordinator for all trading agents"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("master_orchestrator", config)
        self.agents = {}
        self.session_state = {}
        self.load_subagents()
        
    def load_subagents(self):
        """Load and initialize all subagents"""
        from agents.system_init import SystemInitAgent
        from agents.risk_management import RiskManagementAgent
        # ... import all other agents
        
        self.agents = {
            'system_init': SystemInitAgent(self.config),
            'risk_mgmt': RiskManagementAgent(self.config),
            # ... initialize all agents
        }
    
    async def start_session(self) -> str:
        """Initialize and start trading session"""
        self.logger.info("Starting trading session")
        
        # Execute pre-market agents in sequence
        results = {}
        
        # 1. System Initialization
        results['system_init'] = await self.execute_agent('system_init', {})
        if not results['system_init']['system_ready']:
            raise RuntimeError("System initialization failed")
        
        # 2. Risk Management Setup
        results['risk_mgmt'] = await self.execute_agent('risk_mgmt', {
            'account_balance': self.get_account_balance()
        })
        
        # 3. Market Structure Analysis
        results['market_structure'] = await self.execute_agent(
            'market_structure',
            {'symbol': self.config['trading_instrument']}
        )
        
        # ... continue with other agents
        
        session_id = self.generate_session_id()
        self.session_state['id'] = session_id
        self.session_state['start_time'] = datetime.utcnow()
        
        return session_id
    
    async def execute_agent(self, agent_id: str, input_data: Dict) -> Dict:
        """Execute a specific agent and handle results"""
        try:
            agent = self.agents[agent_id]
            result = await agent.execute(input_data)
            self.log_decision(f"{agent_id}_executed", result)
            return result
        except Exception as e:
            return self.handle_error(e)
    
    async def run(self):
        """Main execution loop"""
        while self.is_active():
            # Process trading cycle
            await self.process_cycle()
            await asyncio.sleep(1)
    
    def is_active(self) -> bool:
        """Check if session should continue"""
        # Check session limits, time, etc.
        return True
```

### Step 3: Implement Risk Management Agent

```python
# agents/risk_management.py
from agents.base_agent import BaseAgent
from typing import Dict, Any

class RiskManagementAgent(BaseAgent):
    """Handles all risk calculations and enforcement"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("risk_management", config)
        self.risk_params = config.get('risk_parameters', {})
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution: calculate risk and validate trades"""
        
        account_balance = input_data['account_balance']
        
        # Calculate daily risk parameters
        risk_params = self.calculate_risk_parameters(account_balance)
        
        # Initialize session risk tracking
        session_risk = self.initialize_session_risk(account_balance)
        
        return {
            'status': 'success',
            'risk_parameters': risk_params,
            'session_risk': session_risk
        }
    
    def calculate_position_size(
        self, 
        account_balance: float,
        entry_price: float,
        stop_price: float,
        instrument_spec: Dict
    ) -> Dict[str, Any]:
        """
        YTC Position Sizing Formula:
        Position Size = (Account × Risk%) / (Entry - Stop) / Tick Value
        """
        risk_amount = account_balance * (self.risk_params['risk_per_trade_pct'] / 100)
        stop_distance = abs(entry_price - stop_price)
        
        tick_size = instrument_spec['tick_size']
        tick_value = instrument_spec['tick_value']
        
        stop_distance_ticks = int(stop_distance / tick_size)
        
        if stop_distance_ticks > 0 and tick_value > 0:
            position_size = int(risk_amount / (stop_distance_ticks * tick_value))
        else:
            position_size = 0
        
        actual_risk = position_size * stop_distance_ticks * tick_value
        
        return {
            'position_size_contracts': position_size,
            'risk_amount_target': risk_amount,
            'risk_amount_actual': actual_risk,
            'risk_pct_actual': (actual_risk / account_balance) * 100,
            'stop_distance_ticks': stop_distance_ticks
        }
    
    def validate_trade(
        self,
        trade_request: Dict,
        account_state: Dict
    ) -> Dict[str, Any]:
        """Validate trade against all risk criteria"""
        
        # Check session limit
        if account_state['session_pnl_pct'] <= -self.risk_params['max_session_risk_pct']:
            return {
                'approved': False,
                'reason': 'Session stop loss limit reached'
            }
        
        # Check position count
        if account_state['open_positions'] >= self.risk_params['max_positions']:
            return {
                'approved': False,
                'reason': 'Maximum position count reached'
            }
        
        # Calculate position size
        position_data = self.calculate_position_size(
            account_state['balance'],
            trade_request['entry_price'],
            trade_request['stop_loss'],
            account_state['instrument_spec']
        )
        
        # Validate position size risk
        if position_data['risk_pct_actual'] > self.risk_params['risk_per_trade_pct'] * 1.1:
            return {
                'approved': False,
                'reason': f"Risk {position_data['risk_pct_actual']}% exceeds limit"
            }
        
        return {
            'approved': True,
            'position_data': position_data
        }
```

### Step 4: Create Agent Skills

```python
# skills/pivot_detection.py
import pandas as pd
import numpy as np

class PivotDetectionSkill:
    """YTC Swing Point Detection Skill"""
    
    @staticmethod
    def detect_swing_points(ohlc_data: pd.DataFrame, min_bars: int = 3) -> Dict:
        """
        Identifies swing highs and lows per YTC methodology
        
        Args:
            ohlc_data: DataFrame with OHLC data
            min_bars: Minimum bars on each side for swing point
            
        Returns:
            Dict with swing_highs and swing_lows arrays
        """
        swing_highs = []
        swing_lows = []
        
        for i in range(min_bars, len(ohlc_data) - min_bars):
            # Check for swing high
            current_high = ohlc_data.iloc[i]['high']
            is_swing_high = True
            
            for j in range(1, min_bars + 1):
                left_high = ohlc_data.iloc[i - j]['high']
                right_high = ohlc_data.iloc[i + j]['high']
                
                if left_high >= current_high or right_high >= current_high:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append({
                    'index': i,
                    'price': current_high,
                    'timestamp': ohlc_data.iloc[i]['timestamp']
                })
            
            # Check for swing low (similar logic)
            current_low = ohlc_data.iloc[i]['low']
            is_swing_low = True
            
            for j in range(1, min_bars + 1):
                left_low = ohlc_data.iloc[i - j]['low']
                right_low = ohlc_data.iloc[i + j]['low']
                
                if left_low <= current_low or right_low <= current_low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append({
                    'index': i,
                    'price': current_low,
                    'timestamp': ohlc_data.iloc[i]['timestamp']
                })
        
        return {
            'swing_highs': swing_highs,
            'swing_lows': swing_lows
        }
```

---

## Database Setup

### Step 1: Create Database

```sql
-- Create database and user
CREATE DATABASE ytc_trading;
CREATE USER ytc_trader WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ytc_trading TO ytc_trader;

\c ytc_trading

-- Create schemas
CREATE SCHEMA trading;
CREATE SCHEMA analytics;
CREATE SCHEMA audit;

-- Grant permissions
GRANT ALL ON SCHEMA trading TO ytc_trader;
GRANT ALL ON SCHEMA analytics TO ytc_trader;
GRANT ALL ON SCHEMA audit TO ytc_trader;
```

### Step 2: Create Tables

```sql
-- Session table
CREATE TABLE trading.sessions (
    session_id UUID PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    market VARCHAR(50),
    instrument VARCHAR(50),
    initial_balance DECIMAL(15,2),
    final_balance DECIMAL(15,2),
    session_pnl DECIMAL(15,2),
    trades_count INTEGER,
    status VARCHAR(20)
);

-- Trades table
CREATE TABLE trading.trades (
    trade_id UUID PRIMARY KEY,
    session_id UUID REFERENCES trading.sessions(session_id),
    setup_type VARCHAR(50),
    direction VARCHAR(10),
    entry_time TIMESTAMP,
    entry_price DECIMAL(12,4),
    position_size INTEGER,
    stop_loss DECIMAL(12,4),
    exit_time TIMESTAMP,
    exit_price DECIMAL(12,4),
    pnl DECIMAL(15,2),
    r_multiple DECIMAL(6,2),
    duration_seconds INTEGER
);

-- Agent decisions table
CREATE TABLE audit.agent_decisions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    session_id UUID,
    agent_id VARCHAR(100),
    decision_type VARCHAR(100),
    input_data JSONB,
    output_data JSONB,
    execution_time_ms INTEGER
);

-- Create indexes
CREATE INDEX idx_sessions_start_time ON trading.sessions(start_time);
CREATE INDEX idx_trades_session_id ON trading.trades(session_id);
CREATE INDEX idx_trades_entry_time ON trading.trades(entry_time);
CREATE INDEX idx_agent_decisions_timestamp ON audit.agent_decisions(timestamp);
CREATE INDEX idx_agent_decisions_agent_id ON audit.agent_decisions(agent_id);
```

### Step 3: Database Connection

```python
# database/connection.py
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os

class Database:
    """PostgreSQL database connection manager"""
    
    def __init__(self):
        self.config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', 5432),
            'database': os.getenv('POSTGRES_DB', 'ytc_trading'),
            'user': os.getenv('POSTGRES_USER', 'ytc_trader'),
            'password': os.getenv('POSTGRES_PASSWORD')
        }
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(**self.config)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> list:
        """Execute SELECT query"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
    
    def execute_insert(self, query: str, params: tuple = None) -> int:
        """Execute INSERT query and return ID"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()[0] if cursor.rowcount > 0 else None
```

---

## Testing & Validation

### Step 1: Unit Tests

```python
# tests/test_risk_management.py
import pytest
from agents.risk_management import RiskManagementAgent

def test_position_size_calculation():
    """Test position sizing follows YTC formula"""
    agent = RiskManagementAgent({
        'risk_parameters': {
            'risk_per_trade_pct': 1.0
        }
    })
    
    result = agent.calculate_position_size(
        account_balance=100000,
        entry_price=1.2500,
        stop_price=1.2475,
        instrument_spec={
            'tick_size': 0.0001,
            'tick_value': 10.0
        }
    )
    
    # Risk should be approximately 1% = $1000
    assert 900 <= result['risk_amount_actual'] <= 1100
    assert result['position_size_contracts'] > 0

def test_session_stop_loss_enforcement():
    """Test session stop enforced at -3%"""
    agent = RiskManagementAgent({
        'risk_parameters': {
            'max_session_risk_pct': 3.0
        }
    })
    
    # Simulate -3% drawdown
    validation = agent.validate_trade(
        trade_request={'entry_price': 1.25, 'stop_loss': 1.24},
        account_state={
            'balance': 100000,
            'session_pnl_pct': -3.0,
            'open_positions': 0,
            'instrument_spec': {'tick_size': 0.0001, 'tick_value': 10}
        }
    )
    
    assert validation['approved'] == False
    assert 'stop loss' in validation['reason'].lower()
```

### Step 2: Integration Tests

```bash
# Run integration tests
pytest tests/integration/ -v --cov=agents
```

### Step 3: Backtesting Framework

```python
# backtesting/backtest_engine.py
class BacktestEngine:
    """Backtesting framework for YTC strategy"""
    
    def __init__(self, orchestrator, historical_data):
        self.orchestrator = orchestrator
        self.data = historical_data
        
    async def run_backtest(self, start_date, end_date):
        """Run backtest over historical period"""
        # Implementation
        pass
```

---

## Deployment

### Using Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: ytc_trading
      POSTGRES_USER: ytc_trader
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6.2
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  ytc_system:
    build: .
    depends_on:
      - postgres
      - redis
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - HUMMINGBOT_GATEWAY_URL=${HUMMINGBOT_GATEWAY_URL}
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data

volumes:
  postgres_data:
  redis_data:
```

```bash
# Deploy
docker-compose up -d

# View logs
docker-compose logs -f ytc_system

# Stop
docker-compose down
```

---

## Operational Guide

### Daily Checklist

**Pre-Market (60 min before open)**
- [ ] System health check
- [ ] Review overnight news
- [ ] Check account balance
- [ ] Verify broker connectivity
- [ ] Load session configuration
- [ ] Review previous session lessons

**Market Open**
- [ ] Monitor system initialization
- [ ] Verify agents activated
- [ ] Check structural analysis
- [ ] Confirm risk parameters loaded

**During Session**
- [ ] Monitor real-time dashboard
- [ ] Watch for alerts
- [ ] Track P&L vs limits
- [ ] Review trade executions

**Post-Market**
- [ ] Review session report
- [ ] Analyze performance
- [ ] Update trading journal
- [ ] Set goals for next session

### Monitoring Dashboard

Access at: `http://localhost:8000/dashboard`

Metrics displayed:
- Real-time P&L
- Open positions
- Risk utilization
- Win rate
- System health
- Agent status

### Emergency Procedures

**Connection Loss**
1. System auto-flattens positions
2. Alert sent to operator
3. Attempt reconnection
4. Manual verification required

**Session Stop Hit (-3%)**
1. All orders cancelled
2. Positions closed
3. Trading halted
4. Report generated
5. Review required before restart

---

## Next Steps

1. ✅ Complete environment setup
2. ✅ Implement core agents
3. ✅ Write comprehensive tests
4. ✅ Run paper trading for 30 days
5. ✅ Review and optimize
6. ✅ Start live trading with minimum size
7. ✅ Scale gradually

**Remember**: Start small, test thoroughly, and never risk capital you can't afford to lose.

For questions or issues, refer to individual agent documentation or contact support.

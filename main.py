"""
YTC Trading System - LangSmith Studio
Entry point for LangGraph Studio (langgraph dev)
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
import structlog

from agents.orchestrator import MasterOrchestrator

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def _load_config() -> Dict[str, Any]:
    """Load configuration from .env with defaults"""
    config = {
        # Anthropic
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'model': os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514'),
        'max_tokens': int(os.getenv('MAX_TOKENS', '4096')),
        'gateway_enabled': os.getenv('GATEWAY_ENABLED', 'true').lower() == 'true',

        # Hummingbot Gateway
        'hummingbot_gateway_url': os.getenv('HUMMINGBOT_GATEWAY_URL', 'http://localhost:8000'),
        'hummingbot_username': os.getenv('HUMMINGBOT_USERNAME'),
        'hummingbot_password': os.getenv('HUMMINGBOT_PASSWORD'),
        'connector': os.getenv('CONNECTOR', 'binance_perpetual_testnet'),

        # Account
        'account_config': {
            'initial_balance': float(os.getenv('INITIAL_BALANCE', '100000.0'))
        },

        # Session
        'session_config': {
            'market': os.getenv('TRADING_MARKET', 'crypto'),
            'instrument': os.getenv('TRADING_INSTRUMENT', 'ETH-USDT'),
            'timeframes': {
                'higher': '30min',
                'trading': '3min',
                'lower': '1min'
            },
            'session': {
                'start_time': os.getenv('SESSION_START_TIME', '09:30:00'),
                'duration_hours': int(os.getenv('SESSION_DURATION_HOURS', '3')),
                'timezone': 'America/New_York'
            }
        },

        # Risk Management
        'risk_config': {
            'risk_per_trade_pct': float(os.getenv('RISK_PER_TRADE_PCT', '1.0')),
            'max_session_risk_pct': float(os.getenv('MAX_SESSION_RISK_PCT', '3.0')),
            'max_total_exposure_pct': float(os.getenv('MAX_TOTAL_EXPOSURE_PCT', '3.0')),
            'max_positions': int(os.getenv('MAX_POSITIONS', '3')),
            'max_position_size_lots': 10.0,
            'consecutive_loss_limit': int(os.getenv('CONSECUTIVE_LOSS_LIMIT', '5')),
            'daily_loss_limit_pct': 5.0,
            'correlation_threshold': 0.7,
            'check_correlation': True,
            'max_trade_duration_hours': 4,
            'max_session_trades': 20,
            'emergency_exit_on_connection_loss': True,
            'emergency_exit_timeout_seconds': 30,
            'flatten_on_session_stop': True,
            'allow_partial_contracts': False,
            'strict_mode': True
        },
    }

    # Load agent config from YAML if available
    agent_config_path = 'config/agent_config.yaml'
    if os.path.exists(agent_config_path):
        try:
            import yaml
            with open(agent_config_path, 'r') as f:
                agent_config = yaml.safe_load(f)
                if agent_config:
                    config['agent_config'] = agent_config
        except Exception as e:
            logger.warning("failed_to_load_agent_config", error=str(e))

    return config


# Load .env at import time
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

# Load config at import time
_config = _load_config()


def create_app():
    """
    Create the LangGraph application for LangGraph Studio.
    Called by 'langgraph dev' via langgraph.json.

    Returns:
        Compiled StateGraph workflow
    """
    os.environ['LANGGRAPH_DEV_MODE'] = 'true'
    orchestrator = MasterOrchestrator(_config)
    logger.info("app_created", 
               instrument=_config.get('session_config', {}).get('instrument'))
    return orchestrator.workflow

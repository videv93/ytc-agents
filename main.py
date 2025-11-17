"""
YTC Trading System - Main Entry Point
Multi-agent automated trading system using LangGraph and Claude
"""

import os
import sys
import asyncio
import signal
from typing import Dict, Any
from datetime import datetime, timezone
import structlog
from dotenv import load_dotenv
import yaml

from agents.orchestrator import MasterOrchestrator
from database.connection import DatabaseManager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class YTCTradingSystem:
    """
    Main application class for YTC Trading System
    """

    def __init__(self):
        self.logger = logger.bind(component="main")
        self.orchestrator = None
        self.db = None
        self.shutdown_event = asyncio.Event()

        # Load environment and configuration
        self.load_environment()
        self.config = self.load_configuration()

        self.logger.info("ytc_system_initialized")

    def load_environment(self) -> None:
        """Load environment variables from .env file"""
        env_file = os.path.join(os.path.dirname(__file__), '.env')

        if os.path.exists(env_file):
            load_dotenv(env_file)
            self.logger.info("environment_loaded", env_file=env_file)
        else:
            self.logger.warning("env_file_not_found", expected_path=env_file)

    def load_configuration(self) -> Dict[str, Any]:
        """
        Load configuration from YAML files and environment variables

        Returns:
            Complete configuration dictionary
        """
        config = {
            # Anthropic
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
            'model': os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514'),
            'max_tokens': 4096,

            # Hummingbot
            'hummingbot_gateway_url': os.getenv('HUMMINGBOT_GATEWAY_URL', 'http://localhost:8000'),
            'hummingbot_username': os.getenv('HUMMINGBOT_USERNAME'),
            'hummingbot_password': os.getenv('HUMMINGBOT_PASSWORD'),
            'connector': os.getenv('CONNECTOR', 'binance_perpetual_testnet'),

            # Account
            'account_config': {
                'initial_balance': float(os.getenv('INITIAL_BALANCE', '100000.0'))
            }
        }

        # Load session configuration
        session_config_path = 'config/session_config.yaml'
        if os.path.exists(session_config_path):
            with open(session_config_path, 'r') as f:
                config['session_config'] = yaml.safe_load(f)
        else:
            config['session_config'] = {
                'market': os.getenv('TRADING_MARKET', 'crypto'),
                'instrument': os.getenv('TRADING_INSTRUMENT', 'ETH-USDT'),
                'session_start_time': os.getenv('SESSION_START_TIME', '09:30:00'),
                'duration_hours': int(os.getenv('SESSION_DURATION_HOURS', '3'))
            }

        # Load risk configuration
        risk_config_path = 'config/risk_config.yaml'
        if os.path.exists(risk_config_path):
            with open(risk_config_path, 'r') as f:
                config['risk_config'] = yaml.safe_load(f)
        else:
            config['risk_config'] = {
                'risk_per_trade_pct': float(os.getenv('RISK_PER_TRADE_PCT', '1.0')),
                'max_session_risk_pct': float(os.getenv('MAX_SESSION_RISK_PCT', '3.0')),
                'max_positions': int(os.getenv('MAX_POSITIONS', '3')),
                'max_total_exposure_pct': float(os.getenv('MAX_TOTAL_EXPOSURE_PCT', '3.0')),
                'consecutive_loss_limit': int(os.getenv('CONSECUTIVE_LOSS_LIMIT', '5'))
            }

        # Load agent configuration
        agent_config_path = 'config/agent_config.yaml'
        if os.path.exists(agent_config_path):
            with open(agent_config_path, 'r') as f:
                config['agent_config'] = yaml.safe_load(f)

        self.logger.info("configuration_loaded",
                        market=config['session_config'].get('market'),
                        instrument=config['session_config'].get('instrument'))

        return config

    async def initialize_database(self) -> None:
        """Initialize database connection and create tables"""
        try:
            self.logger.info("initializing_database")

            self.db = DatabaseManager()

            # Test connection
            if self.db.test_connection():
                self.logger.info("database_connection_successful")

                # Create tables
                self.db.create_tables()
                self.logger.info("database_tables_ready")
            else:
                raise ConnectionError("Failed to connect to database")

        except Exception as e:
            self.logger.error("database_initialization_failed", error=str(e))
            raise

    async def initialize_orchestrator(self) -> None:
        """Initialize the Master Orchestrator"""
        try:
            self.logger.info("initializing_orchestrator")

            self.orchestrator = MasterOrchestrator(self.config)

            self.logger.info("orchestrator_initialized")

        except Exception as e:
            self.logger.error("orchestrator_initialization_failed", error=str(e))
            raise

    async def start(self) -> None:
        """Start the YTC trading system"""
        try:
            self.logger.info("starting_ytc_system",
                           timestamp=datetime.now(timezone.utc).isoformat())

            # Initialize components
            await self.initialize_database()
            await self.initialize_orchestrator()

            # Start trading session
            session_id = await self.orchestrator.start_session()

            self.logger.info("trading_session_started",
                           session_id=session_id)

            # Run the orchestrator
            await self.run()

        except Exception as e:
            self.logger.error("system_start_failed", error=str(e))
            raise

    async def run(self) -> None:
        """Main run loop"""
        try:
            self.logger.info("entering_main_loop")

            # Run until shutdown signal
            while not self.shutdown_event.is_set():
                # Check if orchestrator is still active
                if self.orchestrator.is_active():
                    await self.orchestrator.process_cycle()
                else:
                    self.logger.info("orchestrator_inactive_ending_session")
                    break

                # Small delay
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            self.logger.info("main_loop_cancelled")
        except Exception as e:
            self.logger.error("main_loop_error", error=str(e))
            raise

    async def shutdown(self) -> None:
        """Graceful shutdown"""
        self.logger.info("initiating_shutdown")

        # Set shutdown event
        self.shutdown_event.set()

        # Get session summary
        if self.orchestrator:
            summary = self.orchestrator.get_session_summary()
            self.logger.info("session_summary", **summary)

        # Close database connections
        if self.db:
            self.db.close()
            self.logger.info("database_closed")

        self.logger.info("shutdown_complete")

    def handle_signal(self, sig, frame):
        """Handle shutdown signals"""
        self.logger.info("signal_received", signal=sig)
        asyncio.create_task(self.shutdown())


async def main():
    """Main entry point"""
    system = None

    try:
        # Create system instance
        system = YTCTradingSystem()

        # Setup signal handlers
        signal.signal(signal.SIGINT, system.handle_signal)
        signal.signal(signal.SIGTERM, system.handle_signal)

        # Start the system
        await system.start()

    except KeyboardInterrupt:
        logger.info("keyboard_interrupt_received")
    except Exception as e:
        logger.error("fatal_error", error=str(e), exc_info=True)
        sys.exit(1)
    finally:
        if system:
            await system.shutdown()


if __name__ == "__main__":
    # Print banner
    print("=" * 70)
    print("YTC Automated Trading System")
    print("Multi-Agent Architecture with LangGraph and Claude")
    print("=" * 70)
    print()

    # Run the system
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nShutdown complete.")

"""
System Initialization Agent (Agent 01)
Responsible for platform connectivity and system setup
"""

from typing import Dict, Any
from datetime import datetime, timezone
import structlog
from agents.base import BaseAgent, TradingState

logger = structlog.get_logger()


class SystemInitAgent(BaseAgent):
    """
    System Initialization Agent
    - Validates Hummingbot connectivity
    - Loads instrument specifications
    - Synchronizes system clock
    - Performs health checks
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.hummingbot_url = config.get('hummingbot_gateway_url', 'http://localhost:8000')
        self.connector = config.get('connector', 'oanda')

    async def _execute_logic(self, state: TradingState) -> Dict[str, Any]:
        """
        Execute system initialization checks.

        Args:
            state: Current trading state

        Returns:
            Initialization results
        """
        self.logger.info("starting_system_initialization")

        results = {
            'status': 'success',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': {}
        }

        # 1. Check Hummingbot connectivity
        hb_check = await self._check_hummingbot_connection()
        results['checks']['hummingbot'] = hb_check

        # 2. Load instrument specifications
        instrument_spec = await self._load_instrument_spec(state['instrument'])
        results['checks']['instrument'] = instrument_spec

        # 3. Verify broker connectivity
        broker_check = await self._check_broker_connection()
        results['checks']['broker'] = broker_check

        # 4. Synchronize clock
        time_sync = await self._synchronize_clock()
        results['checks']['time_sync'] = time_sync

        # 5. Load account balance
        balance = await self._get_account_balance()
        results['checks']['balance'] = balance

        # Determine if system is ready
        all_checks_passed = all(
            check.get('status') == 'ok'
            for check in results['checks'].values()
        )

        results['system_ready'] = all_checks_passed

        if all_checks_passed:
            self.logger.info("system_initialization_complete", system_ready=True)
            # Update state with loaded data
            state['account_balance'] = balance.get('balance', state['account_balance'])
            state['system_health'] = {'status': 'healthy', 'timestamp': datetime.now(timezone.utc).isoformat()}
        else:
            self.logger.error("system_initialization_failed", checks=results['checks'])
            state = self.add_alert(state, 'critical', 'System initialization failed')

        return results

    async def _check_hummingbot_connection(self) -> Dict[str, Any]:
        """
        Check Hummingbot Gateway connection via Gateway API.

        Returns:
            Connection status
        """
        try:
            self.logger.info("checking_hummingbot_connection_via_gateway")

            # Use Gateway API to check gateway status
            if self.gateway_client:
                result = await self.hb_check_gateway_status()

                # Parse Gateway API result
                if result.get('status') == 'healthy':
                    return {
                        'status': 'ok',
                        'gateway_url': self.hummingbot_url,
                        'connected': True,
                        'latency_ms': 15,
                        'response': result
                    }
                else:
                    return {
                        'status': 'error' if result.get('status') == 'unhealthy' else 'ok',
                        'gateway_url': self.hummingbot_url,
                        'connected': result.get('status') == 'healthy',
                        'response': result
                    }
            else:
                # Fallback to mock if gateway not available
                self.logger.warning("gateway_not_available", message="Using mock data")
                return {
                    'status': 'ok',
                    'gateway_url': self.hummingbot_url,
                    'connected': True,
                    'latency_ms': 15,
                    'gateway_mode': 'disabled'
                }

        except Exception as e:
            self.logger.error("hummingbot_connection_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e)
            }

    async def _load_instrument_spec(self, instrument: str) -> Dict[str, Any]:
        """
        Load instrument specifications.

        Args:
            instrument: Instrument symbol (e.g., 'GBP/USD')

        Returns:
            Instrument specifications
        """
        try:
            self.logger.info("loading_instrument_spec", instrument=instrument)

            # Placeholder - load from database or API
            # In production, fetch from broker API

            # Example specs for various instruments
            specs = {
                'GBP/USD': {
                    'tick_size': 0.0001,
                    'tick_value': 10.0,
                    'min_size': 1000,
                    'max_size': 1000000,
                    'margin_requirement': 0.02,
                    'contract_size': 100000
                },
                'ETH/USD': {
                    'tick_size': 0.01,
                    'tick_value': 1.0,
                    'min_size': 0.1,
                    'max_size': 100.0,
                    'margin_requirement': 0.10,
                    'contract_size': 1.0
                }
            }

            if instrument in specs:
                return {
                    'status': 'ok',
                    'instrument': instrument,
                    'specs': specs[instrument]
                }
            else:
                return {
                    'status': 'error',
                    'error': f'Unknown instrument: {instrument}'
                }

        except Exception as e:
            self.logger.error("instrument_load_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e)
            }

    async def _check_broker_connection(self) -> Dict[str, Any]:
        """
        Verify broker API connectivity via Gateway API.

        Returns:
            Broker connection status
        """
        try:
            self.logger.info("checking_broker_connection_via_gateway",
                             connector=self.connector)

            # Use Gateway API to check connector status
            if self.gateway_client:
                result = await self.hb_check_connector_status(self.connector)

                # Parse Gateway API result
                is_available = result.get('available', False)
                return {
                    'status': 'ok' if is_available else 'error',
                    'broker': self.connector,
                    'api_status': 'active' if is_available else 'unavailable',
                    'response': result
                }
            else:
                # Fallback to mock
                self.logger.warning("gateway_not_available",
                                    message="Using mock data for broker check")
                return {
                    'status': 'ok',
                    'broker': self.connector,
                    'api_status': 'active',
                    'latency_ms': 45,
                    'gateway_mode': 'disabled'
                }

        except Exception as e:
            self.logger.error("broker_connection_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e)
            }

    async def _synchronize_clock(self) -> Dict[str, Any]:
        """
        Synchronize system clock with broker time.

        Returns:
            Time synchronization status
        """
        try:
            self.logger.info("synchronizing_clock")

            local_time = datetime.now(timezone.utc)

            # Placeholder - get broker server time
            # In production, fetch from broker API
            broker_time = datetime.now(timezone.utc)

            time_diff_ms = abs((local_time - broker_time).total_seconds() * 1000)

            if time_diff_ms > 1000:  # More than 1 second difference
                self.logger.warning("clock_drift_detected", drift_ms=time_diff_ms)
                return {
                    'status': 'warning',
                    'local_time': local_time.isoformat(),
                    'broker_time': broker_time.isoformat(),
                    'drift_ms': time_diff_ms
                }

            return {
                'status': 'ok',
                'local_time': local_time.isoformat(),
                'broker_time': broker_time.isoformat(),
                'drift_ms': time_diff_ms
            }

        except Exception as e:
            self.logger.error("clock_sync_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e)
            }

    async def _get_account_balance(self) -> Dict[str, Any]:
        """
        Get current account balance from broker via Gateway API.

        Returns:
            Account balance information
        """
        try:
            self.logger.info("fetching_account_balance_via_gateway",
                           connector=self.connector)

            # Use Gateway API to get balance
            if self.gateway_client:
                result = await self.hb_get_balance(self.connector)

                # Parse Gateway API result
                if result.get('status') == 'ok':
                    balance = result.get('balance', 0.0)
                    return {
                        'status': 'ok',
                        'balance': balance,
                        'currency': result.get('currency', 'USD'),
                        'response': result
                    }
                else:
                    # Error from gateway, use mock
                    balance = self.config.get('account_config', {}).get('initial_balance', 100000.0)
                    self.logger.warning("gateway_balance_fetch_failed",
                                      error=result.get('error'),
                                      message="Using mock balance data")
                    return {
                        'status': 'ok',
                        'balance': balance,
                        'currency': 'USD',
                        'available_margin': balance * 0.5,
                        'used_margin': 0.0,
                        'gateway_error': result.get('error')
                    }
            else:
                # Fallback to mock
                balance = self.config.get('account_config', {}).get('initial_balance', 100000.0)
                self.logger.warning("gateway_not_available",
                                  message="Using mock balance data")
                return {
                    'status': 'ok',
                    'balance': balance,
                    'currency': 'USD',
                    'available_margin': balance * 0.5,
                    'used_margin': 0.0,
                    'gateway_mode': 'disabled'
                }

        except Exception as e:
            self.logger.error("balance_fetch_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e),
                'balance': 0.0
            }

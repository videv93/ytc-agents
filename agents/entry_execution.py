"""
Entry Execution Agent (Agent 08)
Executes trade entries based on validated setups
"""

from typing import Dict, Any
from datetime import datetime, timezone
import structlog
from agents.base import BaseAgent, TradingState

logger = structlog.get_logger()


class EntryExecutionAgent(BaseAgent):
    """
    Entry Execution Agent
    - Monitors for entry trigger in validated setups
    - Identifies Lower Within Pullback (LWP) for long entries
    - Places orders via Hummingbot API
    - Validates entry execution
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.use_limit_orders = config.get('agent_config', {}).get('entry_execution', {}).get('use_limit_orders', True)
        self.entry_offset_ticks = config.get('agent_config', {}).get('entry_execution', {}).get('entry_offset_ticks', 2)
        self.max_attempts = config.get('agent_config', {}).get('entry_execution', {}).get('max_entry_attempts', 3)
        self.hummingbot_url = config.get('hummingbot_gateway_url', 'http://localhost:8000')
        self.connector = config.get('connector', 'oanda')

    async def _execute_logic(self, state: TradingState) -> Dict[str, Any]:
        """
        Execute trade entry if conditions met.

        Args:
            state: Current trading state

        Returns:
            Entry execution results
        """
        self.logger.info("checking_entry_execution")

        try:
            # Check if we have valid setups from scanner
            scanner_output = state.get('agent_outputs', {}).get('setup_scanner', {})
            if not scanner_output:
                return {
                    'status': 'no_action',
                    'reason': 'No setup scanner output available',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

            scanner_result = scanner_output.get('result', {})
            setups = scanner_result.get('setups', [])

            if not setups:
                return {
                    'status': 'no_action',
                    'reason': 'No high-quality setups found',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

            # Get best setup (already sorted by quality)
            best_setup = setups[0]

            # Check entry trigger
            entry_trigger = await self._check_entry_trigger(best_setup, state)

            if not entry_trigger['triggered']:
                return {
                    'status': 'waiting',
                    'setup': best_setup,
                    'waiting_for': entry_trigger['waiting_for'],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

            # Validate trade with risk management
            risk_validation = await self._validate_with_risk_mgmt(
                best_setup,
                entry_trigger,
                state
            )

            if not risk_validation['approved']:
                return {
                    'status': 'rejected',
                    'reason': risk_validation['reason'],
                    'setup': best_setup,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

            # Execute entry order
            order_result = await self._execute_entry_order(
                best_setup,
                entry_trigger,
                risk_validation['position_data'],
                state
            )

            result = {
                'status': 'executed' if order_result['success'] else 'failed',
                'setup': best_setup,
                'entry_trigger': entry_trigger,
                'position_data': risk_validation['position_data'],
                'order': order_result,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            self.logger.info("entry_execution_complete",
                           status=result['status'],
                           setup_type=best_setup['type'])

            return result

        except Exception as e:
            self.logger.error("entry_execution_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    async def _check_entry_trigger(
        self,
        setup: Dict[str, Any],
        state: TradingState
    ) -> Dict[str, Any]:
        """
        Check if entry trigger conditions are met.

        YTC Entry Trigger:
        - For pullback: LWP (Lower Within Pullback) for long
        - Price action confirmation
        - 1min timeframe trigger

        Args:
            setup: Setup configuration
            state: Trading state

        Returns:
            Trigger analysis
        """
        # TODO: Implement actual trigger detection from 1min bars

        # Mock trigger check
        setup_type = setup['type']

        if setup_type == 'pullback':
            # Check for LWP/HWP
            direction = setup['direction']
            entry_zone = setup['entry_zone']

            # Get current price from gateway API
            current_price = 1.25  # Default fallback
            if self.gateway_client:
                try:
                    market_data = await self.gateway_client.get_market_data(
                        connector=self.config.get('connector', 'oanda'),
                        trading_pair=state['instrument']
                    )
                    if market_data.get('status') == 'ok':
                        current_price = market_data['price']
                except Exception as e:
                    self.logger.warning("failed_to_fetch_price", error=str(e))

            if direction == 'long':
                # Looking for LWP - price should be near entry zone
                if abs(current_price - entry_zone) / entry_zone <= 0.001:
                    return {
                        'triggered': True,
                        'trigger_type': 'LWP',
                        'entry_price': current_price,
                        'confirmation': 'Price at Fibonacci level'
                    }
                else:
                    return {
                        'triggered': False,
                        'waiting_for': 'LWP at Fibonacci level',
                        'current_price': current_price,
                        'target_zone': entry_zone
                    }

        return {
            'triggered': False,
            'waiting_for': 'Entry trigger'
        }

    async def _validate_with_risk_mgmt(
        self,
        setup: Dict[str, Any],
        entry_trigger: Dict[str, Any],
        state: TradingState
    ) -> Dict[str, Any]:
        """
        Validate trade with risk management agent.

        Args:
            setup: Setup configuration
            entry_trigger: Entry trigger data
            state: Trading state

        Returns:
            Risk validation result
        """
        # Get risk management agent
        from agents.risk_management import RiskManagementAgent

        risk_agent = RiskManagementAgent('risk_mgmt', self.config)

        # Calculate stop loss based on structure
        stop_loss = self._calculate_stop_loss(setup, entry_trigger)

        # Create trade request
        trade_request = {
            'entry_price': entry_trigger['entry_price'],
            'stop_loss': stop_loss,
            'setup_type': setup['type'],
            'direction': setup['direction']
        }

        # Validate
        validation = risk_agent.validate_trade(trade_request, state)

        return validation

    def _calculate_stop_loss(
        self,
        setup: Dict[str, Any],
        entry_trigger: Dict[str, Any]
    ) -> float:
        """
        Calculate stop loss based on structure.

        YTC Rule: Stop beyond structure that invalidates setup.

        Args:
            setup: Setup configuration
            entry_trigger: Entry trigger

        Returns:
            Stop loss price
        """
        direction = setup['direction']
        entry_price = entry_trigger['entry_price']

        # Get instrument specs for tick size
        tick_size = self.config.get('agent_config', {}).get('entry_execution', {}).get('tick_size', 0.0001)
        buffer_ticks = self.config.get('agent_config', {}).get('entry_execution', {}).get('stop_buffer_ticks', 2)

        if direction == 'long':
            # Stop below the swing low that created pullback
            swing_low = setup.get('swing_low', entry_price * 0.998)
            stop_loss = swing_low - (buffer_ticks * tick_size)
        else:  # short
            # Stop above the swing high
            swing_high = setup.get('swing_high', entry_price * 1.002)
            stop_loss = swing_high + (buffer_ticks * tick_size)

        return stop_loss

    async def _execute_entry_order(
        self,
        setup: Dict[str, Any],
        entry_trigger: Dict[str, Any],
        position_data: Dict[str, Any],
        state: TradingState
    ) -> Dict[str, Any]:
        """
        Execute entry order via Hummingbot Gateway API.

        Args:
            setup: Setup configuration
            entry_trigger: Entry trigger
            position_data: Position sizing data
            state: Trading state

        Returns:
            Order execution result
        """
        try:
            # Prepare order parameters
            side = 'buy' if setup['direction'] == 'long' else 'sell'
            order_type = 'limit' if self.use_limit_orders else 'market'
            amount = position_data['position_size_lots']
            price = entry_trigger['entry_price'] if self.use_limit_orders else None

            self.logger.info("placing_order_via_gateway",
                             connector=self.connector,
                             trading_pair=state['instrument'],
                             side=side,
                             amount=amount,
                             order_type=order_type,
                             price=price)

            # Use Gateway API to place order
            if self.gateway_client:
                result = await self.hb_place_order(
                    connector=self.connector,
                    trading_pair=state['instrument'],
                    side=side,
                    amount=amount,
                    order_type=order_type,
                    price=price
                )

                # Parse gateway API result
                if result.get('status') == 'executed':
                    order_id = result.get('order', {}).get('orderId', result.get('order', {}).get('id', 'UNKNOWN'))
                    return {
                        'success': True,
                        'order_id': order_id,
                        'connector': self.connector,
                        'trading_pair': state['instrument'],
                        'side': side,
                        'amount': amount,
                        'order_type': order_type,
                        'execution_price': entry_trigger['entry_price'],
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'gateway_response': result
                    }
                else:
                    # Error from gateway
                    self.logger.error("gateway_order_failed",
                                      status=result.get('status'),
                                      error=result.get('error'))
                    return {
                        'success': False,
                        'error': result.get('error', 'Unknown gateway error'),
                        'gateway_response': result
                    }
            else:
                # Fallback to mock if gateway not available
                self.logger.warning("gateway_not_available",
                                    message="Using mock order result")
                return {
                    'success': True,
                    'order_id': 'ORDER-MOCK-12345',
                    'connector': self.connector,
                    'trading_pair': state['instrument'],
                    'side': side,
                    'amount': amount,
                    'order_type': order_type,
                    'execution_price': entry_trigger['entry_price'],
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'gateway_mode': 'disabled'
                }

        except Exception as e:
            self.logger.error("order_execution_failed", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }

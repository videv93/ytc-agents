"""
Exit Execution Agent (Agent 10)
Executes all types of trade exits
"""

from typing import Dict, Any
from datetime import datetime, timezone
import structlog
from agents.base import BaseAgent, TradingState

logger = structlog.get_logger()


class ExitExecutionAgent(BaseAgent):
    """
    Exit Execution Agent
    - Executes exits at targets
    - Executes stop losses
    - Time-based exits
    - Signal-based exits
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.exit_types = config.get('agent_config', {}).get('exit_execution', {}).get('exit_types', ['target', 'stop', 'time', 'signal'])
        self.hummingbot_url = config.get('hummingbot_gateway_url', 'http://localhost:8000')
        self.connector = config.get('connector', 'oanda')

    async def _execute_logic(self, state: TradingState) -> Dict[str, Any]:
        """
        Check and execute exits for all positions.

        Skip exit execution if entry_execution status is 'waiting' or 'rejected'.

        Args:
            state: Current trading state

        Returns:
            Exit execution results
        """
        self.logger.info("checking_exits")

        try:
            # Check entry_execution status - skip if waiting or rejected
            agent_outputs = state.get('agent_outputs', {})
            entry_execution_output = agent_outputs.get('entry_execution', {})
            entry_status = entry_execution_output.get('status')

            if entry_status in ['waiting', 'rejected']:
                self.logger.info("skipping_exit_execution",
                               reason=f"entry_execution status is {entry_status}")
                return {
                    'status': 'skipped',
                    'reason': f'Entry execution status is {entry_status}',
                    'entry_execution_status': entry_status,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

            positions = state.get('positions', [])

            if not positions:
                return {
                    'status': 'no_action',
                    'reason': 'No open positions',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

            exits_executed = []

            for position in positions:
                exit_result = await self._check_position_exit(position, state)
                if exit_result and exit_result['should_exit']:
                    # Execute the exit
                    execution = await self._execute_exit(position, exit_result, state)
                    exits_executed.append(execution)

            result = {
                'status': 'success',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'positions_checked': len(positions),
                'exits_executed': len(exits_executed),
                'exits': exits_executed
            }

            self.logger.info("exit_execution_complete",
                           exits=len(exits_executed))

            return result

        except Exception as e:
            self.logger.error("exit_execution_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    async def _check_position_exit(
        self,
        position: Dict[str, Any],
        state: TradingState
    ) -> Dict[str, Any]:
        """
        Check if position should be exited.

        Args:
            position: Position data
            state: Trading state

        Returns:
            Exit decision
        """
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

        # Check target exit
        if 'target' in self.exit_types:
            target_check = self._check_target_exit(position, current_price)
            if target_check['should_exit']:
                return target_check

        # Check stop loss
        if 'stop' in self.exit_types:
            stop_check = self._check_stop_loss_exit(position, current_price)
            if stop_check['should_exit']:
                return stop_check

        # Check time-based exit
        if 'time' in self.exit_types:
            time_check = self._check_time_exit(position)
            if time_check['should_exit']:
                return time_check

        # Check signal-based exit
        if 'signal' in self.exit_types:
            signal_check = self._check_signal_exit(position, state)
            if signal_check['should_exit']:
                return signal_check

        return {'should_exit': False}

    def _check_target_exit(
        self,
        position: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """Check if target is reached"""
        direction = position['direction']
        target = position.get('target_2')  # T2 for remaining position

        if not target:
            return {'should_exit': False}

        if direction == 'long' and current_price >= target:
            return {
                'should_exit': True,
                'exit_type': 'target',
                'exit_price': target,
                'reason': 'T2 target reached'
            }
        elif direction == 'short' and current_price <= target:
            return {
                'should_exit': True,
                'exit_type': 'target',
                'exit_price': target,
                'reason': 'T2 target reached'
            }

        return {'should_exit': False}

    def _check_stop_loss_exit(
        self,
        position: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """Check if stop loss is hit"""
        direction = position['direction']
        stop_loss = position['stop_loss']

        if direction == 'long' and current_price <= stop_loss:
            return {
                'should_exit': True,
                'exit_type': 'stop',
                'exit_price': stop_loss,
                'reason': 'Stop loss hit'
            }
        elif direction == 'short' and current_price >= stop_loss:
            return {
                'should_exit': True,
                'exit_type': 'stop',
                'exit_price': stop_loss,
                'reason': 'Stop loss hit'
            }

        return {'should_exit': False}

    def _check_time_exit(
        self,
        position: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if max time in trade exceeded"""
        entry_time = datetime.fromisoformat(position['entry_time'])
        now = datetime.now(timezone.utc)
        duration = (now - entry_time).total_seconds() / 3600  # hours

        max_duration = 4  # hours

        if duration >= max_duration:
            return {
                'should_exit': True,
                'exit_type': 'time',
                'reason': f'Max duration {max_duration}h exceeded'
            }

        return {'should_exit': False}

    def _check_signal_exit(
        self,
        position: Dict[str, Any],
        state: TradingState
    ) -> Dict[str, Any]:
        """Check for adverse trend signals"""
        trend_data = state.get('trend', {})

        if not trend_data:
            return {'should_exit': False}

        direction = position['direction']
        current_trend = trend_data.get('trend')
        trend_state = trend_data.get('trend_state')

        # Exit if trend is reversing against position
        if direction == 'long' and current_trend == 'downtrend' and trend_state == 'reversing':
            return {
                'should_exit': True,
                'exit_type': 'signal',
                'reason': 'Trend reversal signal'
            }
        elif direction == 'short' and current_trend == 'uptrend' and trend_state == 'reversing':
            return {
                'should_exit': True,
                'exit_type': 'signal',
                'reason': 'Trend reversal signal'
            }

        return {'should_exit': False}

    async def _execute_exit(
        self,
        position: Dict[str, Any],
        exit_decision: Dict[str, Any],
        state: TradingState
    ) -> Dict[str, Any]:
        """
        Execute exit order via Hummingbot Gateway API.

        Args:
            position: Position to exit
            exit_decision: Exit decision data
            state: Trading state

        Returns:
            Execution result
        """
        try:
            # Prepare exit parameters
            side = 'sell' if position['direction'] == 'long' else 'buy'
            amount = position['position_size_lots']

            self.logger.info("executing_exit_via_gateway",
                             connector=self.connector,
                             trading_pair=state['instrument'],
                             side=side,
                             amount=amount,
                             exit_type=exit_decision['exit_type'])

            # Use Gateway API to close position
            if self.gateway_client:
                result = await self.hb_close_position(
                    connector=self.connector,
                    trading_pair=state['instrument'],
                    amount=amount
                )

                # Parse gateway API result
                if result.get('status') == 'executed':
                    order_id = result.get('order', {}).get('orderId', result.get('order', {}).get('id', 'UNKNOWN'))
                    return {
                        'success': True,
                        'position_id': position.get('id'),
                        'exit_type': exit_decision['exit_type'],
                        'exit_price': exit_decision.get('exit_price'),
                        'reason': exit_decision['reason'],
                        'order_id': order_id,
                        'connector': self.connector,
                        'trading_pair': state['instrument'],
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'gateway_response': result
                    }
                else:
                    # Error from gateway
                    self.logger.error("gateway_exit_failed",
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
                                    message="Using mock exit result")
                return {
                    'success': True,
                    'position_id': position.get('id'),
                    'exit_type': exit_decision['exit_type'],
                    'exit_price': exit_decision.get('exit_price'),
                    'reason': exit_decision['reason'],
                    'order_id': 'EXIT-MOCK-12345',
                    'connector': self.connector,
                    'trading_pair': state['instrument'],
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'gateway_mode': 'disabled'
                }

        except Exception as e:
            self.logger.error("exit_execution_failed", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }

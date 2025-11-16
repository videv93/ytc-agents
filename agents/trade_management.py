"""
Trade Management Agent (Agent 09)
Manages open positions with trailing stops and partial exits
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import structlog
from agents.base import BaseAgent, TradingState

logger = structlog.get_logger()


class TradeManagementAgent(BaseAgent):
    """
    Trade Management Agent
    - Trails stops at pivot points
    - Moves to breakeven at +1R
    - Takes partial exits at T1
    - Manages time-based exits
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.breakeven_at_r = config.get('agent_config', {}).get('trade_management', {}).get('move_to_breakeven_at_r', 1.0)
        self.partial_exit_pct = config.get('agent_config', {}).get('trade_management', {}).get('partial_exit_at_t1_pct', 50)
        self.trailing_method = config.get('agent_config', {}).get('trade_management', {}).get('trailing_stop_method', 'pivot')

    async def _execute_logic(self, state: TradingState) -> Dict[str, Any]:
        """
        Manage all open positions.

        Args:
            state: Current trading state

        Returns:
            Trade management results
        """
        self.logger.info("managing_trades",
                        open_positions=state['open_positions_count'])

        try:
            positions = state.get('positions', [])

            if not positions:
                return {
                    'status': 'no_action',
                    'reason': 'No open positions',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

            management_actions = []

            for position in positions:
                actions = await self._manage_position(position, state)
                if actions:
                    management_actions.extend(actions)

            result = {
                'status': 'success',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'positions_managed': len(positions),
                'actions_taken': len(management_actions),
                'actions': management_actions
            }

            self.logger.info("trade_management_complete",
                           actions=len(management_actions))

            return result

        except Exception as e:
            self.logger.error("trade_management_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    async def _manage_position(
        self,
        position: Dict[str, Any],
        state: TradingState
    ) -> List[Dict[str, Any]]:
        """
        Manage a single position.

        Args:
            position: Position data
            state: Trading state

        Returns:
            List of management actions
        """
        actions = []
        
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

        # Calculate R-multiple
        r_multiple = self._calculate_r_multiple(position, current_price)

        # Check for breakeven move
        if r_multiple >= self.breakeven_at_r and position.get('stop_loss') != position.get('entry_price'):
            actions.append({
                'action': 'move_to_breakeven',
                'position_id': position.get('id'),
                'new_stop': position['entry_price'],
                'reason': f'Reached +{self.breakeven_at_r}R'
            })

        # Check for partial exit at T1
        if not position.get('partial_exit_taken') and r_multiple >= 1.0:
            actions.append({
                'action': 'partial_exit',
                'position_id': position.get('id'),
                'exit_percentage': self.partial_exit_pct,
                'exit_price': current_price,
                'reason': 'Reached T1 target'
            })

        # Trail stop
        if self.trailing_method == 'pivot':
            trailing_action = await self._trail_stop_at_pivots(position, state, current_price)
            if trailing_action:
                actions.append(trailing_action)

        return actions

    def _calculate_r_multiple(
        self,
        position: Dict[str, Any],
        current_price: float
    ) -> float:
        """
        Calculate R-multiple for position.

        Args:
            position: Position data
            current_price: Current market price

        Returns:
            R-multiple
        """
        entry_price = position['entry_price']
        stop_loss = position['stop_loss']
        direction = position['direction']

        risk = abs(entry_price - stop_loss)

        if direction == 'long':
            profit = current_price - entry_price
        else:  # short
            profit = entry_price - current_price

        if risk > 0:
            return profit / risk
        return 0.0

    async def _trail_stop_at_pivots(
        self,
        position: Dict[str, Any],
        state: TradingState,
        current_price: float
    ) -> Dict[str, Any]:
        """
        Trail stop loss at pivot points.

        YTC Method: Move stop to below recent higher lows (uptrend)

        Args:
            position: Position data
            state: Trading state
            current_price: Current price

        Returns:
            Trailing stop action or None
        """
        # Get trend data
        trend_data = state.get('trend', {})
        if not trend_data:
            return None

        swing_points = trend_data.get('swing_points', {})
        direction = position['direction']

        if direction == 'long':
            # Trail at higher lows
            recent_lows = swing_points.get('recent_lows', [])
            if recent_lows:
                last_low = recent_lows[-1]['price']

                # Only trail up, never down
                if last_low > position['stop_loss']:
                    # Use instrument specs for tick size
                    tick_size = state.get('agent_outputs', {}).get('system_init', {}).get('result', {}).get('checks', {}).get('instrument', {}).get('specs', {}).get('tick_size', 0.0001)
                    buffer_ticks = 2  # Default 2 ticks buffer
                    return {
                        'action': 'trail_stop',
                        'position_id': position.get('id'),
                        'new_stop': last_low - (buffer_ticks * tick_size),  # Buffer below pivot
                        'reason': 'Trailing at higher low pivot'
                    }

        return None

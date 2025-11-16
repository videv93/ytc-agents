"""
Risk Management Agent (Agent 02)
Handles position sizing, risk calculations, and trade validation
"""

from typing import Dict, Any
from datetime import datetime
import structlog
from agents.base import BaseAgent, TradingState

logger = structlog.get_logger()


class RiskManagementAgent(BaseAgent):
    """
    Risk Management Agent
    - Calculates position sizes using YTC formula
    - Validates trades against risk limits
    - Monitors session risk exposure
    - Enforces stop loss limits
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.risk_config = config.get('risk_config', {})

    async def _execute_logic(self, state: TradingState) -> Dict[str, Any]:
        """
        Execute risk management calculations and updates.

        Args:
            state: Current trading state

        Returns:
            Risk management results
        """
        self.logger.info("executing_risk_management")

        # Calculate risk parameters
        risk_params = self._calculate_risk_parameters(state)

        # Update session risk tracking
        session_risk = self._calculate_session_risk(state)

        # Check risk limits
        risk_checks = self._check_risk_limits(state, session_risk)

        results = {
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'risk_parameters': risk_params,
            'session_risk': session_risk,
            'risk_checks': risk_checks,
            'can_trade': risk_checks['can_trade']
        }

        # Update state with risk parameters
        state['risk_params'] = risk_params
        state['risk_utilization'] = session_risk['risk_utilization_pct']

        # Add alerts if limits are approaching
        if session_risk['risk_utilization_pct'] > 70:
            state = self.add_alert(
                state,
                'warning',
                f"Risk utilization at {session_risk['risk_utilization_pct']:.1f}%"
            )

        if not risk_checks['can_trade']:
            state = self.add_alert(
                state,
                'critical',
                f"Trading halted: {risk_checks['reason']}"
            )

        self.logger.info("risk_management_complete", can_trade=risk_checks['can_trade'])

        return results

    def _calculate_risk_parameters(self, state: TradingState) -> Dict[str, Any]:
        """
        Calculate daily risk parameters.

        Args:
            state: Current trading state

        Returns:
            Risk parameters
        """
        account_balance = state['account_balance']
        risk_per_trade_pct = state['risk_per_trade_pct']
        max_session_risk_pct = state['max_session_risk_pct']
        max_positions = self.risk_config.get('max_positions', 3)

        # Calculate dollar amounts
        risk_per_trade_dollars = account_balance * (risk_per_trade_pct / 100)
        max_session_risk_dollars = account_balance * (max_session_risk_pct / 100)

        # Calculate remaining session risk
        current_loss = min(0, state['session_pnl'])
        remaining_session_risk = max_session_risk_dollars + current_loss

        return {
            'account_balance': account_balance,
            'risk_per_trade_pct': risk_per_trade_pct,
            'risk_per_trade_dollars': risk_per_trade_dollars,
            'max_session_risk_pct': max_session_risk_pct,
            'max_session_risk_dollars': max_session_risk_dollars,
            'remaining_session_risk': remaining_session_risk,
            'max_positions': max_positions,
            'max_total_exposure_pct': self.risk_config.get('max_total_exposure_pct', 3.0)
        }

    def _calculate_session_risk(self, state: TradingState) -> Dict[str, Any]:
        """
        Calculate current session risk exposure.

        Args:
            state: Current trading state

        Returns:
            Session risk metrics
        """
        account_balance = state['account_balance']
        session_pnl = state['session_pnl']
        session_pnl_pct = (session_pnl / account_balance) * 100 if account_balance > 0 else 0

        # Calculate risk from open positions
        positions = state.get('positions', [])
        total_position_risk = sum(pos.get('risk_amount', 0) for pos in positions)
        position_risk_pct = (total_position_risk / account_balance) * 100 if account_balance > 0 else 0

        # Calculate total exposure
        total_exposure = sum(abs(pos.get('notional_value', 0)) for pos in positions)
        exposure_pct = (total_exposure / account_balance) * 100 if account_balance > 0 else 0

        # Risk utilization (how much of max session risk is used)
        max_session_risk = state['max_session_risk_pct']
        risk_used = abs(min(0, session_pnl_pct))
        risk_utilization_pct = (risk_used / max_session_risk) * 100 if max_session_risk > 0 else 0

        return {
            'session_pnl': session_pnl,
            'session_pnl_pct': session_pnl_pct,
            'open_positions': len(positions),
            'total_position_risk': total_position_risk,
            'position_risk_pct': position_risk_pct,
            'total_exposure': total_exposure,
            'exposure_pct': exposure_pct,
            'risk_utilization_pct': risk_utilization_pct,
            'trades_today': len(state.get('trades_today', []))
        }

    def _check_risk_limits(self, state: TradingState, session_risk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if current risk is within limits.

        Args:
            state: Current trading state
            session_risk: Session risk metrics

        Returns:
            Risk limit check results
        """
        checks = {
            'can_trade': True,
            'reason': None,
            'violations': []
        }

        # Check session stop loss
        if session_risk['session_pnl_pct'] <= -state['max_session_risk_pct']:
            checks['can_trade'] = False
            checks['reason'] = 'Session stop loss limit reached'
            checks['violations'].append({
                'type': 'session_stop_loss',
                'current': session_risk['session_pnl_pct'],
                'limit': -state['max_session_risk_pct']
            })

        # Check max positions
        max_positions = self.risk_config.get('max_positions', 3)
        if session_risk['open_positions'] >= max_positions:
            checks['can_trade'] = False
            checks['reason'] = 'Maximum position count reached'
            checks['violations'].append({
                'type': 'max_positions',
                'current': session_risk['open_positions'],
                'limit': max_positions
            })

        # Check max exposure
        max_exposure = self.risk_config.get('max_total_exposure_pct', 3.0)
        if session_risk['exposure_pct'] >= max_exposure:
            checks['can_trade'] = False
            checks['reason'] = 'Maximum exposure limit reached'
            checks['violations'].append({
                'type': 'max_exposure',
                'current': session_risk['exposure_pct'],
                'limit': max_exposure
            })

        # Check consecutive losses (if configured)
        max_consecutive_losses = self.risk_config.get('consecutive_loss_limit', 5)
        consecutive_losses = self._count_consecutive_losses(state)
        if consecutive_losses >= max_consecutive_losses:
            checks['can_trade'] = False
            checks['reason'] = 'Consecutive loss limit reached'
            checks['violations'].append({
                'type': 'consecutive_losses',
                'current': consecutive_losses,
                'limit': max_consecutive_losses
            })

        return checks

    def _count_consecutive_losses(self, state: TradingState) -> int:
        """
        Count consecutive losing trades.

        Args:
            state: Current trading state

        Returns:
            Number of consecutive losses
        """
        trades = state.get('trades_today', [])
        if not trades:
            return 0

        consecutive = 0
        for trade in reversed(trades):
            if trade.get('pnl', 0) < 0:
                consecutive += 1
            else:
                break

        return consecutive

    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_price: float,
        instrument_spec: Dict[str, Any],
        risk_pct: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate position size using YTC formula.

        Formula: Position Size = (Account × Risk%) / (Entry - Stop) / Tick Value

        Args:
            account_balance: Current account balance
            entry_price: Proposed entry price
            stop_price: Stop loss price
            instrument_spec: Instrument specifications
            risk_pct: Risk percentage (default 1.0%)

        Returns:
            Position sizing details
        """
        risk_amount = account_balance * (risk_pct / 100)
        stop_distance = abs(entry_price - stop_price)

        tick_size = instrument_spec.get('tick_size', 0.0001)
        tick_value = instrument_spec.get('tick_value', 10.0)
        min_size = instrument_spec.get('min_size', 1000)
        max_size = instrument_spec.get('max_size', 1000000)

        # Calculate stop distance in ticks
        stop_distance_ticks = int(stop_distance / tick_size) if tick_size > 0 else 0

        # Calculate position size
        if stop_distance_ticks > 0 and tick_value > 0:
            position_size = risk_amount / (stop_distance_ticks * tick_value)

            # Round to contract size
            contract_size = instrument_spec.get('contract_size', 1000)
            position_size_contracts = int(position_size / contract_size) * contract_size

            # Enforce min/max limits
            position_size_contracts = max(min_size, min(position_size_contracts, max_size))

        else:
            position_size_contracts = 0

        # Calculate actual risk with rounded position size
        actual_risk = position_size_contracts / instrument_spec.get('contract_size', 1000) * stop_distance_ticks * tick_value
        actual_risk_pct = (actual_risk / account_balance) * 100 if account_balance > 0 else 0

        return {
            'position_size_contracts': position_size_contracts,
            'position_size_lots': position_size_contracts / instrument_spec.get('contract_size', 1000),
            'risk_amount_target': risk_amount,
            'risk_amount_actual': actual_risk,
            'risk_pct_target': risk_pct,
            'risk_pct_actual': actual_risk_pct,
            'stop_distance': stop_distance,
            'stop_distance_ticks': stop_distance_ticks,
            'entry_price': entry_price,
            'stop_price': stop_price
        }

    def validate_trade(
        self,
        trade_request: Dict[str, Any],
        state: TradingState
    ) -> Dict[str, Any]:
        """
        Validate a trade request against all risk criteria.

        Args:
            trade_request: Trade request details
            state: Current trading state

        Returns:
            Validation result
        """
        # Get session risk
        session_risk = self._calculate_session_risk(state)

        # Check risk limits
        risk_checks = self._check_risk_limits(state, session_risk)

        if not risk_checks['can_trade']:
            return {
                'approved': False,
                'reason': risk_checks['reason'],
                'violations': risk_checks['violations']
            }

        # Get instrument specs from system init agent output
        system_init = state.get('agent_outputs', {}).get('system_init', {})
        instrument_check = system_init.get('result', {}).get('checks', {}).get('instrument', {})
        instrument_spec = instrument_check.get('specs', {})

        if not instrument_spec:
            return {
                'approved': False,
                'reason': 'Instrument specifications not loaded'
            }

        # Calculate position size
        position_data = self.calculate_position_size(
            account_balance=state['account_balance'],
            entry_price=trade_request['entry_price'],
            stop_price=trade_request['stop_loss'],
            instrument_spec=instrument_spec,
            risk_pct=state['risk_per_trade_pct']
        )

        # Validate position size risk (allow 10% tolerance)
        max_allowed_risk = state['risk_per_trade_pct'] * 1.1
        if position_data['risk_pct_actual'] > max_allowed_risk:
            return {
                'approved': False,
                'reason': f"Risk {position_data['risk_pct_actual']:.2f}% exceeds limit {max_allowed_risk:.2f}%",
                'position_data': position_data
            }

        return {
            'approved': True,
            'position_data': position_data,
            'session_risk': session_risk
        }

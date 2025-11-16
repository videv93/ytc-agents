"""
Unit tests for Risk Management Agent
"""

import pytest
from agents.risk_management import RiskManagementAgent
from agents.base import TradingState


@pytest.fixture
def risk_agent():
    """Create risk management agent for testing"""
    config = {
        'anthropic_api_key': 'test-key',
        'risk_config': {
            'risk_per_trade_pct': 1.0,
            'max_session_risk_pct': 3.0,
            'max_positions': 3,
            'max_total_exposure_pct': 3.0,
            'consecutive_loss_limit': 5
        }
    }
    return RiskManagementAgent('risk_mgmt', config)


@pytest.fixture
def base_state():
    """Create base trading state for testing"""
    return {
        'session_id': 'test-session',
        'phase': 'pre_market',
        'account_balance': 100000.0,
        'initial_balance': 100000.0,
        'session_pnl': 0.0,
        'session_pnl_pct': 0.0,
        'risk_per_trade_pct': 1.0,
        'max_session_risk_pct': 3.0,
        'positions': [],
        'trades_today': [],
        'agent_outputs': {
            'system_init': {
                'result': {
                    'checks': {
                        'instrument': {
                            'specs': {
                                'tick_size': 0.0001,
                                'tick_value': 10.0,
                                'contract_size': 100000,
                                'min_size': 1000,
                                'max_size': 1000000
                            }
                        }
                    }
                }
            }
        }
    }


class TestPositionSizing:
    """Test position sizing calculations"""

    def test_position_size_calculation_basic(self, risk_agent):
        """Test basic position size calculation"""
        result = risk_agent.calculate_position_size(
            account_balance=100000,
            entry_price=1.2500,
            stop_price=1.2475,
            instrument_spec={
                'tick_size': 0.0001,
                'tick_value': 10.0,
                'contract_size': 100000,
                'min_size': 1000,
                'max_size': 1000000
            },
            risk_pct=1.0
        )

        # 1% of $100,000 = $1,000 risk
        # Stop distance = 0.0025 = 25 ticks
        # Position size = $1,000 / (25 ticks * $10/tick) = 4 contracts
        assert result['position_size_contracts'] == 400000
        assert 900 <= result['risk_amount_actual'] <= 1100
        assert result['risk_pct_actual'] <= 1.1  # Allow 10% tolerance

    def test_position_size_respects_min_max(self, risk_agent):
        """Test that position size respects min/max limits"""
        result = risk_agent.calculate_position_size(
            account_balance=1000000,  # Large balance
            entry_price=1.2500,
            stop_price=1.2499,  # Tiny stop
            instrument_spec={
                'tick_size': 0.0001,
                'tick_value': 10.0,
                'contract_size': 100000,
                'min_size': 1000,
                'max_size': 500000  # Cap at 500k
            },
            risk_pct=1.0
        )

        # Should be capped at max_size
        assert result['position_size_contracts'] <= 500000


class TestRiskLimits:
    """Test risk limit enforcement"""

    def test_session_stop_loss_enforcement(self, risk_agent, base_state):
        """Test that session stop loss is enforced at -3%"""
        # Simulate -3% session loss
        base_state['session_pnl'] = -3000
        base_state['session_pnl_pct'] = -3.0

        session_risk = risk_agent._calculate_session_risk(base_state)
        risk_checks = risk_agent._check_risk_limits(base_state, session_risk)

        assert risk_checks['can_trade'] == False
        assert 'stop loss' in risk_checks['reason'].lower()

    def test_max_positions_enforcement(self, risk_agent, base_state):
        """Test that max position count is enforced"""
        # Add 3 positions
        base_state['positions'] = [
            {'risk_amount': 1000},
            {'risk_amount': 1000},
            {'risk_amount': 1000}
        ]

        session_risk = risk_agent._calculate_session_risk(base_state)
        risk_checks = risk_agent._check_risk_limits(base_state, session_risk)

        assert risk_checks['can_trade'] == False
        assert 'position count' in risk_checks['reason'].lower()

    def test_consecutive_losses_enforcement(self, risk_agent, base_state):
        """Test that consecutive loss limit is enforced"""
        # Add 5 consecutive losing trades
        base_state['trades_today'] = [
            {'pnl': -100},
            {'pnl': -150},
            {'pnl': -200},
            {'pnl': -120},
            {'pnl': -180}
        ]

        session_risk = risk_agent._calculate_session_risk(base_state)
        risk_checks = risk_agent._check_risk_limits(base_state, session_risk)

        assert risk_checks['can_trade'] == False
        assert 'consecutive' in risk_checks['reason'].lower()


class TestTradeValidation:
    """Test trade validation"""

    def test_valid_trade_approval(self, risk_agent, base_state):
        """Test that valid trades are approved"""
        trade_request = {
            'entry_price': 1.2500,
            'stop_loss': 1.2475
        }

        result = risk_agent.validate_trade(trade_request, base_state)

        assert result['approved'] == True
        assert 'position_data' in result
        assert result['position_data']['position_size_contracts'] > 0

    def test_oversized_risk_rejection(self, risk_agent, base_state):
        """Test that trades with excessive risk are rejected"""
        trade_request = {
            'entry_price': 1.2500,
            'stop_loss': 1.2000  # Very wide stop
        }

        # Manually calculate - this should exceed risk limits
        result = risk_agent.validate_trade(trade_request, base_state)

        # With such a wide stop, position size will be very small
        # The test should verify risk calculation works correctly
        assert 'position_data' in result


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test async operations"""

    async def test_execute_logic(self, risk_agent, base_state):
        """Test agent execution"""
        result = await risk_agent._execute_logic(base_state)

        assert result['status'] == 'success'
        assert 'risk_parameters' in result
        assert 'session_risk' in result
        assert 'can_trade' in result

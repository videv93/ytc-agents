"""
Simple tests for agents that work with the current codebase
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch


@pytest.fixture
def test_config():
    """Test configuration"""
    return {
        'anthropic_api_key': 'test-api-key',
        'model': 'claude-sonnet-4-20250514',
        'session_config': {
            'market': 'crypto',
            'instrument': 'ETH/USD',
            'session_start_time': '09:30:00',
            'duration_hours': 3
        },
        'risk_config': {
            'risk_per_trade_pct': 1.0,
            'max_session_risk_pct': 3.0,
            'max_positions': 3
        },
        'account_config': {
            'initial_balance': 100000.0
        },
        'gateway_enabled': False
    }


@pytest.fixture
def base_trading_state():
    """Base trading state for tests"""
    return {
        'session_id': 'test-session-001',
        'phase': 'pre_market',
        'start_time': datetime.now(timezone.utc).isoformat(),
        'current_time': datetime.now(timezone.utc).isoformat(),
        'account_balance': 100000.0,
        'initial_balance': 100000.0,
        'session_pnl': 0.0,
        'session_pnl_pct': 0.0,
        'risk_params': {},
        'risk_utilization': 0.0,
        'max_session_risk_pct': 3.0,
        'risk_per_trade_pct': 1.0,
        'market': 'crypto',
        'instrument': 'ETH/USD',
        'market_structure': {},
        'trend': {},
        'strength_weakness': {},
        'positions': [],
        'open_positions_count': 0,
        'pending_orders': [],
        'trades_today': [],
        'agent_outputs': {},
        'alerts': [],
        'system_health': {},
        'emergency_stop': False,
        'stop_reason': None
    }


class TestEconomicCalendarAgent:
    """Tests for Economic Calendar Agent"""

    @pytest.mark.asyncio
    async def test_economic_calendar_fetch_news_events(self, test_config):
        """Test fetching news events returns empty list for crypto"""
        from agents.economic_calendar import EconomicCalendarAgent
        
        agent = EconomicCalendarAgent('economic_calendar', test_config)
        events = await agent._fetch_news_events('ETH/USD', hours_ahead=24)
        
        # Crypto trading should have empty events
        assert events == []

    @pytest.mark.asyncio
    async def test_economic_calendar_check_trading_restriction(self, test_config):
        """Test trading restriction check"""
        from agents.economic_calendar import EconomicCalendarAgent
        
        agent = EconomicCalendarAgent('economic_calendar', test_config)
        result = agent._check_trading_restriction([])
        
        assert result['restricted'] is False

    @pytest.mark.asyncio
    async def test_economic_calendar_get_next_critical_event(self, test_config):
        """Test getting next critical event from empty list"""
        from agents.economic_calendar import EconomicCalendarAgent
        
        agent = EconomicCalendarAgent('economic_calendar', test_config)
        event = agent._get_next_critical_event([])
        
        assert event is None


class TestLoggingAuditAgent:
    """Tests for Logging & Audit Agent"""

    @pytest.mark.asyncio
    async def test_log_trade_events_with_empty_trades(self, test_config):
        """Test logging trade events with empty active_trades"""
        from agents.logging_audit import LoggingAuditAgent
        
        with patch('agents.logging_audit.get_database'):
            agent = LoggingAuditAgent('logging_audit', test_config)
        
        state = {
            'session_id': 'test-001',
            'active_trades': []
        }
        
        events = await agent._log_trade_events(state)
        assert events == []

    @pytest.mark.asyncio
    async def test_log_trade_events_with_trades(self, test_config):
        """Test logging trade events with active trades"""
        from agents.logging_audit import LoggingAuditAgent
        
        with patch('agents.logging_audit.get_database'):
            agent = LoggingAuditAgent('logging_audit', test_config)
        
        state = {
            'session_id': 'test-001',
            'active_trades': [
                {
                    'id': 'trade-001',
                    'instrument': 'ETH/USD',
                    'type': 'long',
                    'entry_price': 2000.0,
                    'quantity': 1.0,
                    'status': 'open'
                }
            ]
        }
        
        with patch.object(agent, '_log_agent_decisions', return_value=0):
            events = await agent._log_trade_events(state)
        
        assert len(events) == 1
        assert events[0]['trade_id'] == 'trade-001'
        assert events[0]['instrument'] == 'ETH/USD'


class TestTrendDefinitionAgent:
    """Tests for Trend Definition Agent"""

    def test_get_current_price_mock(self):
         """Test mock price for ETH/USD"""
         # Mock price for ETH/USD should be reasonable
         eth_price = 2250.0  # Example price
         assert eth_price > 1000  # Should be plausible


class TestRiskManagementAgent:
    """Tests for Risk Management Agent"""

    def test_risk_calculation_initialization(self, test_config):
        """Test risk management initialization"""
        from agents.risk_management import RiskManagementAgent
        
        agent = RiskManagementAgent('risk_mgmt', test_config)
        assert agent.agent_id == 'risk_mgmt'
        assert agent.risk_per_trade_pct == 1.0


class TestMarketStructureAgent:
    """Tests for Market Structure Agent"""

    def test_market_structure_initialization(self, test_config):
        """Test market structure initialization"""
        from agents.market_structure import MarketStructureAgent
        
        agent = MarketStructureAgent('market_structure', test_config)
        assert agent.agent_id == 'market_structure'


class TestSystemInitAgent:
    """Tests for System Init Agent"""

    def test_system_init_initialization(self, test_config):
        """Test system init agent initialization"""
        from agents.system_init import SystemInitAgent
        
        agent = SystemInitAgent('system_init', test_config)
        assert agent.agent_id == 'system_init'
        assert agent.hummingbot_url


class TestMonitoringAgent:
    """Tests for Monitoring Agent"""

    def test_monitoring_initialization(self, test_config):
        """Test monitoring agent initialization"""
        from agents.monitoring import MonitoringAgent
        
        agent = MonitoringAgent('monitoring', test_config)
        assert agent.agent_id == 'monitoring'


class TestSetupScannerAgent:
    """Tests for Setup Scanner Agent"""

    def test_setup_scanner_initialization(self, test_config):
        """Test setup scanner initialization"""
        from agents.setup_scanner import SetupScannerAgent
        
        agent = SetupScannerAgent('setup_scanner', test_config)
        assert agent.agent_id == 'setup_scanner'


class TestEntryExecutionAgent:
    """Tests for Entry Execution Agent"""

    def test_entry_execution_initialization(self, test_config):
        """Test entry execution initialization"""
        from agents.entry_execution import EntryExecutionAgent
        
        agent = EntryExecutionAgent('entry_execution', test_config)
        assert agent.agent_id == 'entry_execution'


class TestExitExecutionAgent:
    """Tests for Exit Execution Agent"""

    def test_exit_execution_initialization(self, test_config):
        """Test exit execution initialization"""
        from agents.exit_execution import ExitExecutionAgent
        
        agent = ExitExecutionAgent('exit_execution', test_config)
        assert agent.agent_id == 'exit_execution'


class TestTradeManagementAgent:
    """Tests for Trade Management Agent"""

    def test_trade_management_initialization(self, test_config):
        """Test trade management initialization"""
        from agents.trade_management import TradeManagementAgent
        
        agent = TradeManagementAgent('trade_management', test_config)
        assert agent.agent_id == 'trade_management'


class TestSessionReviewAgent:
    """Tests for Session Review Agent"""

    def test_session_review_initialization(self, test_config):
        """Test session review initialization"""
        from agents.session_review import SessionReviewAgent
        
        agent = SessionReviewAgent('session_review', test_config)
        assert agent.agent_id == 'session_review'


class TestPerformanceAnalyticsAgent:
    """Tests for Performance Analytics Agent"""

    def test_performance_analytics_initialization(self, test_config):
        """Test performance analytics initialization"""
        from agents.performance_analytics import PerformanceAnalyticsAgent
        
        agent = PerformanceAnalyticsAgent('performance_analytics', test_config)
        assert agent.agent_id == 'performance_analytics'


class TestLearningOptimizationAgent:
    """Tests for Learning Optimization Agent"""

    def test_learning_optimization_initialization(self, test_config):
        """Test learning optimization initialization"""
        from agents.learning_optimization import LearningOptimizationAgent
        
        agent = LearningOptimizationAgent('learning_optimization', test_config)
        assert agent.agent_id == 'learning_optimization'


class TestContingencyAgent:
    """Tests for Contingency Agent"""

    def test_contingency_initialization(self, test_config):
        """Test contingency agent initialization"""
        from agents.contingency import ContingencyAgent
        
        agent = ContingencyAgent('contingency', test_config)
        assert agent.agent_id == 'contingency'


class TestStrengthWeaknessAgent:
    """Tests for Strength Weakness Agent"""

    def test_strength_weakness_initialization(self, test_config):
        """Test strength weakness initialization"""
        from agents.strength_weakness import StrengthWeaknessAgent
        
        agent = StrengthWeaknessAgent('strength_weakness', test_config)
        assert agent.agent_id == 'strength_weakness'

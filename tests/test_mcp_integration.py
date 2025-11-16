"""
Tests for MCP Integration with Hummingbot
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.mcp_client import HummingbotMCPClient
from agents.base import BaseAgent, TradingState
from anthropic import Anthropic


class TestHummingbotMCPClient:
    """Test suite for HummingbotMCPClient"""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create a mock Anthropic client"""
        client = Mock(spec=Anthropic)
        return client

    @pytest.fixture
    def mcp_client(self, mock_anthropic_client):
        """Create HummingbotMCPClient instance"""
        return HummingbotMCPClient(
            anthropic_client=mock_anthropic_client,
            model="claude-sonnet-4-20250514"
        )

    def test_client_initialization(self, mcp_client):
        """Test MCP client initializes correctly"""
        assert mcp_client is not None
        assert mcp_client.model == "claude-sonnet-4-20250514"
        assert len(mcp_client.tools) == 10  # Should have 10 tools defined

    def test_tools_definition(self, mcp_client):
        """Test that all expected tools are defined"""
        tool_names = [tool['name'] for tool in mcp_client.tools]

        expected_tools = [
            'place_order',
            'cancel_order',
            'get_balance',
            'get_positions',
            'get_market_data',
            'get_order_status',
            'check_gateway_status',
            'check_connector_status',
            'get_open_orders',
            'close_position'
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Tool {expected_tool} not found"

    def test_tool_schemas(self, mcp_client):
        """Test that tool schemas are valid"""
        for tool in mcp_client.tools:
            assert 'name' in tool
            assert 'description' in tool
            assert 'input_schema' in tool
            assert tool['input_schema']['type'] == 'object'
            assert 'properties' in tool['input_schema']

    @pytest.mark.asyncio
    async def test_place_order_helper(self, mcp_client):
        """Test place_order helper method"""
        # Mock the Claude API response
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"

        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.name = "place_order"
        mock_tool_use.id = "tool_123"
        mock_tool_use.input = {
            "connector": "oanda",
            "trading_pair": "GBP/USD",
            "side": "buy",
            "amount": 1.0,
            "order_type": "market"
        }

        mock_response.content = [mock_tool_use]
        mcp_client.client.messages.create = Mock(return_value=mock_response)

        # Test the method
        result = await mcp_client.place_order(
            connector="oanda",
            trading_pair="GBP/USD",
            side="buy",
            amount=1.0,
            order_type="market"
        )

        assert result is not None
        assert result['status'] == 'would_execute'
        assert result['tool'] == 'place_order'

    @pytest.mark.asyncio
    async def test_get_balance_helper(self, mcp_client):
        """Test get_balance helper method"""
        # Mock the Claude API response
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"

        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.name = "get_balance"
        mock_tool_use.id = "tool_456"
        mock_tool_use.input = {"connector": "oanda"}

        mock_response.content = [mock_tool_use]
        mcp_client.client.messages.create = Mock(return_value=mock_response)

        # Test the method
        result = await mcp_client.get_balance(connector="oanda")

        assert result is not None
        assert result['status'] == 'would_execute'
        assert result['tool'] == 'get_balance'


class TestBaseAgentMCPIntegration:
    """Test MCP integration in BaseAgent"""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return {
            'anthropic_api_key': 'test-key-12345',
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 4096,
            'mcp_enabled': True,
            'timeout_seconds': 60,
            'retry_attempts': 3
        }

    @pytest.fixture
    def mock_agent(self, mock_config):
        """Create a concrete implementation of BaseAgent for testing"""
        class TestAgent(BaseAgent):
            async def _execute_logic(self, state: TradingState):
                return {'status': 'success'}

        with patch('agents.base.MCP_CLIENT_AVAILABLE', True):
            with patch('agents.base.HummingbotMCPClient'):
                agent = TestAgent('test_agent', mock_config)
                return agent

    def test_agent_mcp_initialization(self, mock_config):
        """Test that BaseAgent initializes MCP client when enabled"""
        class TestAgent(BaseAgent):
            async def _execute_logic(self, state: TradingState):
                return {'status': 'success'}

        with patch('agents.base.MCP_CLIENT_AVAILABLE', True):
            with patch('agents.base.HummingbotMCPClient') as MockMCPClient:
                agent = TestAgent('test_agent', mock_config)

                # Verify MCP client was initialized
                assert agent.mcp_enabled is True
                MockMCPClient.assert_called_once()

    def test_agent_mcp_disabled(self):
        """Test that MCP can be disabled"""
        class TestAgent(BaseAgent):
            async def _execute_logic(self, state: TradingState):
                return {'status': 'success'}

        config = {
            'anthropic_api_key': 'test-key',
            'mcp_enabled': False
        }

        agent = TestAgent('test_agent', config)
        assert agent.mcp_enabled is False
        assert agent.mcp_client is None

    @pytest.mark.asyncio
    async def test_hb_place_order_without_mcp(self):
        """Test that hb_place_order raises error when MCP not available"""
        class TestAgent(BaseAgent):
            async def _execute_logic(self, state: TradingState):
                return {'status': 'success'}

        config = {
            'anthropic_api_key': 'test-key',
            'mcp_enabled': False
        }

        agent = TestAgent('test_agent', config)

        with pytest.raises(RuntimeError, match="MCP client not initialized"):
            await agent.hb_place_order(
                connector="oanda",
                trading_pair="GBP/USD",
                side="buy",
                amount=1.0
            )


class TestAgentMCPMethods:
    """Test MCP helper methods in BaseAgent"""

    @pytest.fixture
    def mock_agent_with_mcp(self):
        """Create agent with mocked MCP client"""
        class TestAgent(BaseAgent):
            async def _execute_logic(self, state: TradingState):
                return {'status': 'success'}

        config = {
            'anthropic_api_key': 'test-key',
            'mcp_enabled': True
        }

        with patch('agents.base.MCP_CLIENT_AVAILABLE', True):
            with patch('agents.base.HummingbotMCPClient'):
                agent = TestAgent('test_agent', config)

                # Mock the MCP client methods
                agent.mcp_client = AsyncMock()
                agent.mcp_client.place_order = AsyncMock(return_value={'success': True})
                agent.mcp_client.get_balance = AsyncMock(return_value={'balance': 10000})
                agent.mcp_client.get_positions = AsyncMock(return_value={'positions': []})
                agent.mcp_client.close_position = AsyncMock(return_value={'success': True})
                agent.mcp_client.check_gateway_status = AsyncMock(return_value={'status': 'healthy'})
                agent.mcp_client.check_connector_status = AsyncMock(return_value={'available': True})
                agent.mcp_client.get_market_data = AsyncMock(return_value={'price': 1.2500})

                return agent

    @pytest.mark.asyncio
    async def test_hb_place_order(self, mock_agent_with_mcp):
        """Test hb_place_order wrapper method"""
        result = await mock_agent_with_mcp.hb_place_order(
            connector="oanda",
            trading_pair="GBP/USD",
            side="buy",
            amount=1.0
        )

        assert result['success'] is True
        mock_agent_with_mcp.mcp_client.place_order.assert_called_once()

    @pytest.mark.asyncio
    async def test_hb_get_balance(self, mock_agent_with_mcp):
        """Test hb_get_balance wrapper method"""
        result = await mock_agent_with_mcp.hb_get_balance(connector="oanda")

        assert 'balance' in result
        mock_agent_with_mcp.mcp_client.get_balance.assert_called_once_with("oanda")

    @pytest.mark.asyncio
    async def test_hb_get_positions(self, mock_agent_with_mcp):
        """Test hb_get_positions wrapper method"""
        result = await mock_agent_with_mcp.hb_get_positions(
            connector="oanda",
            trading_pair="GBP/USD"
        )

        assert 'positions' in result
        mock_agent_with_mcp.mcp_client.get_positions.assert_called_once()

    @pytest.mark.asyncio
    async def test_hb_close_position(self, mock_agent_with_mcp):
        """Test hb_close_position wrapper method"""
        result = await mock_agent_with_mcp.hb_close_position(
            connector="oanda",
            trading_pair="GBP/USD"
        )

        assert result['success'] is True
        mock_agent_with_mcp.mcp_client.close_position.assert_called_once()

    @pytest.mark.asyncio
    async def test_hb_check_gateway_status(self, mock_agent_with_mcp):
        """Test hb_check_gateway_status wrapper method"""
        result = await mock_agent_with_mcp.hb_check_gateway_status()

        assert result['status'] == 'healthy'
        mock_agent_with_mcp.mcp_client.check_gateway_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_hb_check_connector_status(self, mock_agent_with_mcp):
        """Test hb_check_connector_status wrapper method"""
        result = await mock_agent_with_mcp.hb_check_connector_status(connector="oanda")

        assert result['available'] is True
        mock_agent_with_mcp.mcp_client.check_connector_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_hb_get_market_data(self, mock_agent_with_mcp):
        """Test hb_get_market_data wrapper method"""
        result = await mock_agent_with_mcp.hb_get_market_data(
            connector="oanda",
            trading_pair="GBP/USD"
        )

        assert 'price' in result
        mock_agent_with_mcp.mcp_client.get_market_data.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
Base Agent Framework for YTC Trading System
Uses LangGraph for state management and workflow orchestration
"""

from typing import TypedDict, Any, Dict, List, Optional, Annotated
from datetime import datetime
from abc import ABC, abstractmethod
import structlog
from anthropic import Anthropic
import os
import json
import sys

# Add tools directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

try:
    from mcp_client import HummingbotMCPClient
    MCP_CLIENT_AVAILABLE = True
except ImportError:
    MCP_CLIENT_AVAILABLE = False

logger = structlog.get_logger()


class TradingState(TypedDict):
    """
    Shared state across all agents in the trading system.
    This state is passed through the LangGraph workflow.
    """
    # Session Info
    session_id: str
    phase: str  # pre_market, session_open, active_trading, post_market, shutdown
    start_time: str
    current_time: str

    # Account State
    account_balance: float
    initial_balance: float
    session_pnl: float
    session_pnl_pct: float

    # Risk Management
    risk_params: Dict[str, Any]
    risk_utilization: float
    max_session_risk_pct: float
    risk_per_trade_pct: float

    # Market State
    market: str
    instrument: str
    market_structure: Dict[str, Any]
    trend: Dict[str, Any]
    strength_weakness: Dict[str, Any]

    # Trading State
    positions: List[Dict[str, Any]]
    open_positions_count: int
    pending_orders: List[Dict[str, Any]]
    trades_today: List[Dict[str, Any]]

    # Agent Outputs
    agent_outputs: Dict[str, Any]

    # Alerts & Monitoring
    alerts: List[Dict[str, Any]]
    system_health: Dict[str, Any]

    # Emergency
    emergency_stop: bool
    stop_reason: Optional[str]


class AgentConfig(TypedDict):
    """Configuration for individual agents"""
    agent_id: str
    enabled: bool
    timeout_seconds: int
    retry_attempts: int
    log_level: str
    model: str
    max_tokens: int


class BaseAgent(ABC):
    """
    Base class for all YTC trading agents.
    Integrates with LangGraph for stateful workflow execution.
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        """
        Initialize base agent.

        Args:
            agent_id: Unique identifier for this agent
            config: Configuration dictionary
        """
        self.agent_id = agent_id
        self.config = config
        self.logger = logger.bind(agent_id=agent_id)

        # Initialize Anthropic client
        api_key = config.get('anthropic_api_key') or os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in config or environment")

        self.client = Anthropic(api_key=api_key)
        self.model = config.get('model', 'claude-sonnet-4-20250514')
        self.max_tokens = config.get('max_tokens', 4096)

        # Agent-specific settings
        self.timeout = config.get('timeout_seconds', 60)
        self.retry_attempts = config.get('retry_attempts', 3)

        # Initialize MCP client for Hummingbot integration
        self.mcp_enabled = config.get('mcp_enabled', True)
        self.mcp_client = None
        if self.mcp_enabled and MCP_CLIENT_AVAILABLE:
            self.mcp_client = HummingbotMCPClient(self.client, self.model)
            self.logger.info("mcp_client_initialized")
        elif self.mcp_enabled and not MCP_CLIENT_AVAILABLE:
            self.logger.warning("mcp_client_not_available",
                              message="MCP client requested but not available")

        self.logger.info("agent_initialized", config=self.config)

    async def execute(self, state: TradingState) -> TradingState:
        """
        Main execution method called by LangGraph.
        This is the interface that LangGraph uses.

        Args:
            state: Current trading state

        Returns:
            Updated trading state
        """
        self.logger.info("agent_execution_start",
                        phase=state.get('phase'),
                        session_id=state.get('session_id'))

        try:
            # Call the agent-specific logic
            result = await self._execute_logic(state)

            # Update state with agent output
            updated_state = self._update_state(state, result)

            # Log the decision
            self._log_decision(result, updated_state)

            self.logger.info("agent_execution_complete",
                           agent_id=self.agent_id,
                           success=True)

            return updated_state

        except Exception as e:
            self.logger.error("agent_execution_failed",
                            error=str(e),
                            agent_id=self.agent_id)
            return self._handle_error(state, e)

    @abstractmethod
    async def _execute_logic(self, state: TradingState) -> Dict[str, Any]:
        """
        Agent-specific execution logic.
        Must be implemented by each agent.

        Args:
            state: Current trading state

        Returns:
            Dictionary containing agent's output
        """
        pass

    async def call_claude(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None
    ) -> Any:
        """
        Call Claude API with the given prompt.

        Args:
            prompt: User prompt for Claude
            system_prompt: Optional system prompt
            tools: Optional list of tools for Claude to use

        Returns:
            Claude API response
        """
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        if tools:
            kwargs["tools"] = tools

        self.logger.debug("calling_claude",
                         prompt_length=len(prompt),
                         has_tools=bool(tools))

        response = self.client.messages.create(**kwargs)

        return response

    def build_prompt(self, state: TradingState, additional_context: str = "") -> str:
        """
        Build a prompt for Claude based on current state.
        Can be overridden by subclasses for agent-specific prompts.

        Args:
            state: Current trading state
            additional_context: Additional context to include

        Returns:
            Formatted prompt string
        """
        prompt = f"""
You are the {self.agent_id} agent in the YTC automated trading system.

Current State:
- Phase: {state.get('phase')}
- Session ID: {state.get('session_id')}
- Account Balance: ${state.get('account_balance', 0):,.2f}
- Session P&L: ${state.get('session_pnl', 0):,.2f} ({state.get('session_pnl_pct', 0):.2f}%)
- Open Positions: {state.get('open_positions_count', 0)}
- Instrument: {state.get('instrument')}

{additional_context}

Please analyze the current state and provide your output.
"""
        return prompt

    def _update_state(self, state: TradingState, result: Dict[str, Any]) -> TradingState:
        """
        Update the trading state with agent's output.

        Args:
            state: Current state
            result: Agent's output

        Returns:
            Updated state
        """
        # Create a copy of the state
        updated_state = state.copy()

        # Store agent output
        if 'agent_outputs' not in updated_state:
            updated_state['agent_outputs'] = {}

        updated_state['agent_outputs'][self.agent_id] = {
            'timestamp': datetime.utcnow().isoformat(),
            'result': result,
            'status': result.get('status', 'success')
        }

        # Update current time
        updated_state['current_time'] = datetime.utcnow().isoformat()

        return updated_state

    def _log_decision(self, result: Dict[str, Any], state: TradingState) -> None:
        """
        Log agent decision for audit trail.

        Args:
            result: Agent's output
            state: Updated state
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'agent_id': self.agent_id,
            'session_id': state.get('session_id'),
            'phase': state.get('phase'),
            'result': result,
            'state_snapshot': {
                'account_balance': state.get('account_balance'),
                'session_pnl': state.get('session_pnl'),
                'positions': len(state.get('positions', []))
            }
        }

        self.logger.info("agent_decision", **log_entry)

    def _handle_error(self, state: TradingState, error: Exception) -> TradingState:
        """
        Handle errors during agent execution.

        Args:
            state: Current state
            error: The exception that occurred

        Returns:
            State with error information
        """
        updated_state = state.copy()

        error_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'agent_id': self.agent_id,
            'error': str(error),
            'error_type': type(error).__name__
        }

        # Add to alerts
        if 'alerts' not in updated_state:
            updated_state['alerts'] = []

        updated_state['alerts'].append({
            'severity': 'critical',
            'message': f"Agent {self.agent_id} failed: {str(error)}",
            'timestamp': datetime.utcnow().isoformat()
        })

        # Store error in agent outputs
        if 'agent_outputs' not in updated_state:
            updated_state['agent_outputs'] = {}

        updated_state['agent_outputs'][self.agent_id] = {
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'error',
            'error': error_info
        }

        return updated_state

    def validate_state(self, state: TradingState, required_fields: List[str]) -> bool:
        """
        Validate that required fields exist in state.

        Args:
            state: State to validate
            required_fields: List of required field names

        Returns:
            True if all required fields present
        """
        for field in required_fields:
            if field not in state:
                self.logger.warning("missing_required_field", field=field)
                return False
        return True

    def add_alert(
        self,
        state: TradingState,
        severity: str,
        message: str
    ) -> TradingState:
        """
        Add an alert to the state.

        Args:
            state: Current state
            severity: Alert severity (info, warning, critical)
            message: Alert message

        Returns:
            Updated state with alert
        """
        if 'alerts' not in state:
            state['alerts'] = []

        state['alerts'].append({
            'severity': severity,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'agent_id': self.agent_id
        })

        return state

    # ===== MCP Integration Methods =====

    async def hb_place_order(
        self,
        connector: str,
        trading_pair: str,
        side: str,
        amount: float,
        order_type: str = "market",
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Place order via Hummingbot MCP.

        Args:
            connector: Exchange connector (e.g., 'oanda')
            trading_pair: Trading pair (e.g., 'GBP/USD')
            side: 'buy' or 'sell'
            amount: Position size
            order_type: 'market' or 'limit'
            price: Limit price (for limit orders)

        Returns:
            Order result from Hummingbot
        """
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")

        self.logger.info("placing_order_via_mcp",
                        connector=connector,
                        pair=trading_pair,
                        side=side,
                        amount=amount)

        return await self.mcp_client.place_order(
            connector=connector,
            trading_pair=trading_pair,
            side=side,
            amount=amount,
            order_type=order_type,
            price=price
        )

    async def hb_get_balance(self, connector: str) -> Dict[str, Any]:
        """
        Get account balance via Hummingbot MCP.

        Args:
            connector: Exchange connector

        Returns:
            Balance information
        """
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")

        return await self.mcp_client.get_balance(connector)

    async def hb_get_positions(
        self,
        connector: str,
        trading_pair: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get open positions via Hummingbot MCP.

        Args:
            connector: Exchange connector
            trading_pair: Optional filter by trading pair

        Returns:
            Positions information
        """
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")

        return await self.mcp_client.get_positions(connector, trading_pair)

    async def hb_close_position(
        self,
        connector: str,
        trading_pair: str,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Close position via Hummingbot MCP.

        Args:
            connector: Exchange connector
            trading_pair: Trading pair
            amount: Amount to close (None = close all)

        Returns:
            Close result
        """
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")

        return await self.mcp_client.close_position(connector, trading_pair, amount)

    async def hb_check_gateway_status(self) -> Dict[str, Any]:
        """
        Check Hummingbot Gateway health via MCP.

        Returns:
            Gateway status
        """
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")

        return await self.mcp_client.check_gateway_status()

    async def hb_check_connector_status(self, connector: str) -> Dict[str, Any]:
        """
        Check connector availability via MCP.

        Args:
            connector: Connector name

        Returns:
            Connector status
        """
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")

        return await self.mcp_client.check_connector_status(connector)

    async def hb_get_market_data(
        self,
        connector: str,
        trading_pair: str
    ) -> Dict[str, Any]:
        """
        Get market data via MCP.

        Args:
            connector: Exchange connector
            trading_pair: Trading pair

        Returns:
            Market data
        """
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")

        return await self.mcp_client.get_market_data(connector, trading_pair)


class AgentResponse(TypedDict):
    """Standard response format from agents"""
    status: str  # success, failure, partial
    data: Dict[str, Any]
    message: str
    timestamp: str
    next_actions: List[str]

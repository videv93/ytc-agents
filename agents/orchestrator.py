"""
Master Orchestrator Agent
Central coordinator for all YTC trading agents using LangGraph
"""

from typing import Dict, Any, Literal
from datetime import datetime, timedelta
import uuid
import structlog
from langgraph.graph import StateGraph, END
from agents.base import TradingState, BaseAgent

logger = structlog.get_logger()


class MasterOrchestrator:
    """
    Master Orchestrator coordinates all agents through the trading cycle.
    Uses LangGraph for workflow management and state persistence.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Master Orchestrator.

        Args:
            config: Configuration dictionary containing:
                - anthropic_api_key
                - session_config
                - risk_config
                - agent_configs
        """
        self.config = config
        self.logger = logger.bind(component="master_orchestrator")

        # Initialize session state
        self.session_state: TradingState = self._initialize_state()

        # Build the LangGraph workflow
        self.workflow = self._build_workflow()

        self.logger.info("orchestrator_initialized")

    def _initialize_state(self) -> TradingState:
        """
        Initialize the trading state for a new session.

        Returns:
            Initial TradingState
        """
        session_config = self.config.get('session_config', {})
        risk_config = self.config.get('risk_config', {})

        initial_balance = self.config.get('account_config', {}).get('initial_balance', 100000.0)

        state: TradingState = {
            # Session Info
            'session_id': str(uuid.uuid4()),
            'phase': 'pre_market',
            'start_time': datetime.utcnow().isoformat(),
            'current_time': datetime.utcnow().isoformat(),

            # Account State
            'account_balance': initial_balance,
            'initial_balance': initial_balance,
            'session_pnl': 0.0,
            'session_pnl_pct': 0.0,

            # Risk Management
            'risk_params': risk_config,
            'risk_utilization': 0.0,
            'max_session_risk_pct': risk_config.get('max_session_risk_pct', 3.0),
            'risk_per_trade_pct': risk_config.get('risk_per_trade_pct', 1.0),

            # Market State
            'market': session_config.get('market', 'forex'),
            'instrument': session_config.get('instrument', 'GBP/USD'),
            'market_structure': {},
            'trend': {},
            'strength_weakness': {},

            # Trading State
            'positions': [],
            'open_positions_count': 0,
            'pending_orders': [],
            'trades_today': [],

            # Agent Outputs
            'agent_outputs': {},

            # Alerts & Monitoring
            'alerts': [],
            'system_health': {'status': 'initializing'},

            # Emergency
            'emergency_stop': False,
            'stop_reason': None
        }

        return state

    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow with all agents.

        Returns:
            Compiled StateGraph
        """
        # Create the state graph
        workflow = StateGraph(TradingState)

        # Lazy import agents to avoid circular dependencies
        from agents.system_init import SystemInitAgent
        from agents.risk_management import RiskManagementAgent
        # More agents will be imported as they're implemented

        # Initialize agents
        self.agents = {
            'system_init': SystemInitAgent('system_init', self.config),
            'risk_mgmt': RiskManagementAgent('risk_mgmt', self.config),
            # More agents will be added
        }

        # Add nodes for Pre-Market phase
        workflow.add_node("system_init", self.agents['system_init'].execute)
        workflow.add_node("risk_mgmt", self.agents['risk_mgmt'].execute)

        # Add routing/control nodes
        workflow.add_node("check_phase", self._check_phase_transition)
        workflow.add_node("emergency_check", self._check_emergency)

        # Define the workflow edges
        # Entry point
        workflow.set_entry_point("system_init")

        # Pre-market sequence
        workflow.add_edge("system_init", "risk_mgmt")
        workflow.add_edge("risk_mgmt", "emergency_check")

        # Emergency check routing
        workflow.add_conditional_edges(
            "emergency_check",
            self._route_emergency,
            {
                "continue": "check_phase",
                "stop": END
            }
        )

        # Phase transition routing
        workflow.add_conditional_edges(
            "check_phase",
            self._route_by_phase,
            {
                "pre_market": "system_init",  # Loop in pre-market until market opens
                "session_open": END,  # Will expand this later
                "active_trading": END,  # Will expand this later
                "post_market": END,  # Will expand this later
                "shutdown": END
            }
        )

        # Compile the workflow
        compiled_workflow = workflow.compile()

        self.logger.info("workflow_built", nodes=len(workflow.nodes))

        return compiled_workflow

    async def start_session(self) -> str:
        """
        Start a new trading session.

        Returns:
            Session ID
        """
        self.logger.info("starting_session",
                        session_id=self.session_state['session_id'])

        try:
            # Execute the workflow
            final_state = await self.workflow.ainvoke(self.session_state)

            # Update our state
            self.session_state = final_state

            self.logger.info("session_started",
                           session_id=self.session_state['session_id'],
                           phase=self.session_state['phase'])

            return self.session_state['session_id']

        except Exception as e:
            self.logger.error("session_start_failed", error=str(e))
            raise

    async def run(self) -> None:
        """
        Main execution loop.
        Runs continuously until session ends or emergency stop.
        """
        self.logger.info("orchestrator_running")

        try:
            while self.is_active():
                # Process one cycle
                await self.process_cycle()

                # Small delay to prevent tight loop
                import asyncio
                await asyncio.sleep(1)

        except Exception as e:
            self.logger.error("orchestrator_error", error=str(e))
            await self.emergency_shutdown(str(e))

    async def process_cycle(self) -> None:
        """Process one trading cycle"""
        self.logger.debug("processing_cycle", phase=self.session_state['phase'])

        # Execute workflow with current state
        updated_state = await self.workflow.ainvoke(self.session_state)

        # Update our state
        self.session_state = updated_state

    def is_active(self) -> bool:
        """
        Check if the session should continue running.

        Returns:
            True if session should continue
        """
        # Check emergency stop
        if self.session_state.get('emergency_stop'):
            return False

        # Check session duration
        start_time = datetime.fromisoformat(self.session_state['start_time'])
        max_duration = self.config.get('session_config', {}).get('duration_hours', 4)
        if datetime.utcnow() - start_time > timedelta(hours=max_duration):
            self.logger.info("session_timeout")
            return False

        # Check if in shutdown phase
        if self.session_state['phase'] == 'shutdown':
            return False

        return True

    async def _check_phase_transition(self, state: TradingState) -> TradingState:
        """
        Check and perform phase transitions.

        Args:
            state: Current state

        Returns:
            Updated state
        """
        current_phase = state['phase']
        self.logger.debug("checking_phase_transition", current_phase=current_phase)

        # Phase transition logic
        # This is a simplified version - expand based on actual requirements

        if current_phase == 'pre_market':
            # Check if market is open
            if self._is_market_open():
                state['phase'] = 'session_open'
                self.logger.info("phase_transition", from_phase='pre_market', to_phase='session_open')

        elif current_phase == 'session_open':
            # After initial analysis, move to active trading
            # Check if trend analysis is complete
            if 'trend' in state.get('agent_outputs', {}):
                state['phase'] = 'active_trading'
                self.logger.info("phase_transition", from_phase='session_open', to_phase='active_trading')

        elif current_phase == 'active_trading':
            # Check if session should end
            session_config = self.config.get('session_config', {})
            duration_hours = session_config.get('duration_hours', 3)
            start_time = datetime.fromisoformat(state['start_time'])

            if datetime.utcnow() - start_time > timedelta(hours=duration_hours):
                state['phase'] = 'post_market'
                self.logger.info("phase_transition", from_phase='active_trading', to_phase='post_market')

        elif current_phase == 'post_market':
            # After review, shutdown
            if 'session_review' in state.get('agent_outputs', {}):
                state['phase'] = 'shutdown'
                self.logger.info("phase_transition", from_phase='post_market', to_phase='shutdown')

        return state

    async def _check_emergency(self, state: TradingState) -> TradingState:
        """
        Check for emergency conditions.

        Args:
            state: Current state

        Returns:
            Updated state
        """
        # Check session P&L limit
        if state['session_pnl_pct'] <= -state['max_session_risk_pct']:
            self.logger.critical("emergency_stop_triggered",
                               reason="session_loss_limit",
                               pnl_pct=state['session_pnl_pct'])
            state['emergency_stop'] = True
            state['stop_reason'] = f"Session loss limit reached: {state['session_pnl_pct']:.2f}%"

        # Check system health
        system_health = state.get('system_health', {})
        if system_health.get('status') == 'critical':
            self.logger.critical("emergency_stop_triggered", reason="system_health")
            state['emergency_stop'] = True
            state['stop_reason'] = "Critical system health issue"

        return state

    def _route_emergency(self, state: TradingState) -> Literal["continue", "stop"]:
        """
        Route based on emergency status.

        Args:
            state: Current state

        Returns:
            Routing decision
        """
        if state.get('emergency_stop'):
            return "stop"
        return "continue"

    def _route_by_phase(
        self,
        state: TradingState
    ) -> Literal["pre_market", "session_open", "active_trading", "post_market", "shutdown"]:
        """
        Route to appropriate phase.

        Args:
            state: Current state

        Returns:
            Phase to route to
        """
        return state['phase']

    def _is_market_open(self) -> bool:
        """
        Check if market is open.
        This is a placeholder - implement actual market hours logic.

        Returns:
            True if market is open
        """
        # Placeholder implementation
        # In production, check actual market hours
        now = datetime.utcnow()
        session_start = self.config.get('session_config', {}).get('session_start_time', '09:30:00')

        # Simple time-based check (needs proper timezone handling)
        return True  # For now, always return True for testing

    async def emergency_shutdown(self, reason: str) -> None:
        """
        Execute emergency shutdown procedure.

        Args:
            reason: Reason for emergency shutdown
        """
        self.logger.critical("emergency_shutdown_initiated", reason=reason)

        # Set emergency stop
        self.session_state['emergency_stop'] = True
        self.session_state['stop_reason'] = reason
        self.session_state['phase'] = 'shutdown'

        # Cancel all orders
        # Close all positions
        # Generate emergency report

        self.logger.critical("emergency_shutdown_complete")

    def get_state(self) -> TradingState:
        """
        Get current trading state.

        Returns:
            Current TradingState
        """
        return self.session_state

    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of current session.

        Returns:
            Session summary
        """
        return {
            'session_id': self.session_state['session_id'],
            'phase': self.session_state['phase'],
            'duration': self._get_session_duration(),
            'pnl': self.session_state['session_pnl'],
            'pnl_pct': self.session_state['session_pnl_pct'],
            'trades': len(self.session_state.get('trades_today', [])),
            'positions': self.session_state['open_positions_count'],
            'alerts': len(self.session_state.get('alerts', []))
        }

    def _get_session_duration(self) -> float:
        """
        Calculate session duration in hours.

        Returns:
            Duration in hours
        """
        start = datetime.fromisoformat(self.session_state['start_time'])
        duration = datetime.utcnow() - start
        return duration.total_seconds() / 3600

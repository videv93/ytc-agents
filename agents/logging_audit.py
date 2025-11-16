"""
Logging & Audit Agent (Agent 17)
Maintains comprehensive audit trail of all decisions and actions
"""

from typing import Dict, Any, List
from datetime import datetime
import structlog
from agents.base import BaseAgent, TradingState
from database.connection import get_database
from database.models import AgentDecision, Session

logger = structlog.get_logger()


class LoggingAuditAgent(BaseAgent):
    """
    Logging & Audit Agent
    - Logs all agent decisions
    - Records all trade actions
    - Maintains audit trail
    - Ensures compliance
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.log_all_decisions = config.get('agent_config', {}).get('logging_audit', {}).get('log_all_decisions', True)
        self.db = get_database()

    async def _execute_logic(self, state: TradingState) -> Dict[str, Any]:
        """
        Log and audit all system activity.

        Args:
            state: Current trading state

        Returns:
            Logging results
        """
        try:
            # Ensure session exists in database
            await self._ensure_session_exists(state)

            # Log agent outputs
            logged_count = await self._log_agent_decisions(state)

            # Log trade events
            trade_logs = await self._log_trade_events(state)

            result = {
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat(),
                'decisions_logged': logged_count,
                'trade_events_logged': len(trade_logs)
            }

            return result

        except Exception as e:
            self.logger.error("logging_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    async def _ensure_session_exists(self, state: TradingState) -> None:
        """Ensure session record exists in database"""
        session_id = state['session_id']
        
        try:
            with self.db.get_session() as db_session:
                # Check if session already exists
                existing = db_session.query(Session).filter_by(session_id=session_id).first()
                if existing:
                    return
                
                # Create new session record
                session = Session(
                    session_id=session_id,
                    market=state.get('market', 'forex'),
                    instrument=state.get('instrument', 'GBP/USD'),
                    initial_balance=state.get('initial_balance', 100000.0),
                    status='active'
                )
                db_session.add(session)
        except Exception as e:
            self.logger.error("session_creation_failed", session_id=session_id, error=str(e))
            raise

    async def _log_agent_decisions(self, state: TradingState) -> int:
        """Log all agent decisions to database"""
        count = 0
        agent_outputs = state.get('agent_outputs', {})

        for agent_id, output in agent_outputs.items():
            try:
                with self.db.get_session() as session:
                    decision = AgentDecision(
                        session_id=state['session_id'],
                        agent_id=agent_id,
                        decision_type='execution',
                        input_data={},
                        output_data=output,
                        status=output.get('status', 'unknown')
                    )
                    session.add(decision)
                    count += 1
            except Exception as e:
                self.logger.error("decision_log_failed", agent=agent_id, error=str(e))

        return count

    async def _log_trade_events(self, state: TradingState) -> List[Dict[str, Any]]:
        """Log trade-related events"""
        events = []
        # TODO: Implement trade event logging
        return events

"""
Next Session Prep Agent (Agent 15)
Prepares for the next trading session
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
import structlog
from agents.base import BaseAgent, TradingState

logger = structlog.get_logger()


class NextSessionPrepAgent(BaseAgent):
    """
    Next Session Prep Agent
    - Sets goals for next session
    - Identifies focus areas
    - Updates trading calendar
    - Generates preparation checklist
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)

    async def _execute_logic(self, state: TradingState) -> Dict[str, Any]:
        """
        Prepare for next session.

        Args:
            state: Current trading state

        Returns:
            Preparation results
        """
        self.logger.info("preparing_next_session")

        try:
            # Review session results
            session_review = state.get('agent_outputs', {}).get('session_review', {})

            # Set goals
            goals = self._set_next_session_goals(session_review, state)

            # Identify focus areas
            focus_areas = self._identify_focus_areas(session_review)

            # Generate checklist
            checklist = self._generate_checklist(goals, focus_areas)

            result = {
                'status': 'success',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'next_session_date': (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat(),
                'goals': goals,
                'focus_areas': focus_areas,
                'checklist': checklist
            }

            return result

        except Exception as e:
            self.logger.error("next_session_prep_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    def _set_next_session_goals(self, review: Dict, state: TradingState) -> List[str]:
        """Set process goals for next session"""
        return [
            "Execute only high-quality setups (score >= 75)",
            "Wait for confirmation before entry",
            "Manage stops according to plan"
        ]

    def _identify_focus_areas(self, review: Dict) -> List[str]:
        """Identify areas to focus on"""
        return [
            "Entry timing and patience",
            "Stop loss placement"
        ]

    def _generate_checklist(self, goals: List[str], focus: List[str]) -> List[Dict]:
        """Generate preparation checklist"""
        return [
            {'item': 'Review previous session lessons', 'completed': False},
            {'item': 'Check economic calendar', 'completed': False},
            {'item': 'Set process goals', 'completed': True},
            {'item': 'Verify platform connectivity', 'completed': False}
        ]

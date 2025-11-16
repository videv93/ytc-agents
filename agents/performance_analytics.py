"""
Performance Analytics Agent (Agent 13)
Calculates performance metrics and statistics
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import structlog
from agents.base import BaseAgent, TradingState

logger = structlog.get_logger()


class PerformanceAnalyticsAgent(BaseAgent):
    """
    Performance Analytics Agent
    - Calculates win rate, profit factor, expectancy
    - Updates performance journal
    - Tracks statistical metrics
    - Monitors trend analysis
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)

    async def _execute_logic(self, state: TradingState) -> Dict[str, Any]:
        """
        Calculate performance analytics.

        Args:
            state: Current trading state

        Returns:
            Analytics results
        """
        self.logger.info("calculating_analytics")

        try:
            trades = state.get('trades_today', [])

            # Calculate metrics
            metrics = {
                'win_rate': self._calculate_win_rate(trades),
                'profit_factor': self._calculate_profit_factor(trades),
                'expectancy': self._calculate_expectancy(trades),
                'avg_win_r': self._calculate_avg_win_r(trades),
                'avg_loss_r': self._calculate_avg_loss_r(trades),
                'largest_win_r': self._get_largest_win(trades),
                'largest_loss_r': self._get_largest_loss(trades)
            }

            result = {
                'status': 'success',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'metrics': metrics,
                'trades_analyzed': len(trades)
            }

            return result

        except Exception as e:
            self.logger.error("analytics_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    def _calculate_win_rate(self, trades: List[Dict]) -> float:
        """Calculate win rate percentage"""
        if not trades:
            return 0.0
        winners = sum(1 for t in trades if t.get('pnl', 0) > 0)
        return (winners / len(trades)) * 100

    def _calculate_profit_factor(self, trades: List[Dict]) -> float:
        """Calculate profit factor"""
        gross_profit = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0)
        gross_loss = abs(sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0))
        return gross_profit / gross_loss if gross_loss > 0 else 0.0

    def _calculate_expectancy(self, trades: List[Dict]) -> float:
        """Calculate expectancy in R"""
        if not trades:
            return 0.0
        total_r = sum(t.get('r_multiple', 0) for t in trades)
        return total_r / len(trades)

    def _calculate_avg_win_r(self, trades: List[Dict]) -> float:
        """Calculate average winning R"""
        winners = [t.get('r_multiple', 0) for t in trades if t.get('pnl', 0) > 0]
        return sum(winners) / len(winners) if winners else 0.0

    def _calculate_avg_loss_r(self, trades: List[Dict]) -> float:
        """Calculate average losing R"""
        losers = [t.get('r_multiple', 0) for t in trades if t.get('pnl', 0) < 0]
        return sum(losers) / len(losers) if losers else 0.0

    def _get_largest_win(self, trades: List[Dict]) -> float:
        """Get largest win in R"""
        winners = [t.get('r_multiple', 0) for t in trades if t.get('pnl', 0) > 0]
        return max(winners) if winners else 0.0

    def _get_largest_loss(self, trades: List[Dict]) -> float:
        """Get largest loss in R"""
        losers = [t.get('r_multiple', 0) for t in trades if t.get('pnl', 0) < 0]
        return min(losers) if losers else 0.0

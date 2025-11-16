"""
Real-Time Monitoring Agent (Agent 11)
Monitors system health and trading metrics in real-time
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import structlog
from agents.base import BaseAgent, TradingState

logger = structlog.get_logger()


class RealTimeMonitoringAgent(BaseAgent):
    """
    Real-Time Monitoring Agent
    - Monitors system health continuously
    - Tracks P&L and risk utilization
    - Detects anomalies
    - Generates alerts
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.check_interval = config.get('agent_config', {}).get('real_time_monitoring', {}).get('check_interval_seconds', 5)
        self.alert_thresholds = config.get('agent_config', {}).get('real_time_monitoring', {}).get('alert_thresholds', {})

    async def _execute_logic(self, state: TradingState) -> Dict[str, Any]:
        """
        Monitor system and generate alerts.

        Args:
            state: Current trading state

        Returns:
            Monitoring results
        """
        self.logger.debug("monitoring_system")

        try:
            alerts_generated = []

            # Monitor P&L
            pnl_alerts = self._check_pnl_alerts(state)
            alerts_generated.extend(pnl_alerts)

            # Monitor risk utilization
            risk_alerts = self._check_risk_alerts(state)
            alerts_generated.extend(risk_alerts)

            # Monitor position health
            position_alerts = self._check_position_health(state)
            alerts_generated.extend(position_alerts)

            # Monitor system health
            system_alerts = self._check_system_health(state)
            alerts_generated.extend(system_alerts)

            result = {
                'status': 'success',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'alerts_generated': len(alerts_generated),
                'alerts': alerts_generated,
                'system_status': 'healthy' if not any(a['severity'] == 'critical' for a in alerts_generated) else 'degraded'
            }

            # Add alerts to state
            for alert in alerts_generated:
                state = self.add_alert(state, alert['severity'], alert['message'])

            return result

        except Exception as e:
            self.logger.error("monitoring_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    def _check_pnl_alerts(self, state: TradingState) -> List[Dict[str, Any]]:
        """Check P&L thresholds"""
        alerts = []
        pnl_pct = state.get('session_pnl_pct', 0)
        warning_threshold = self.alert_thresholds.get('pnl_warning_pct', -2.0)

        if pnl_pct <= warning_threshold:
            alerts.append({
                'severity': 'warning',
                'message': f'Session P&L at {pnl_pct:.2f}%',
                'metric': 'pnl',
                'value': pnl_pct
            })

        return alerts

    def _check_risk_alerts(self, state: TradingState) -> List[Dict[str, Any]]:
        """Check risk utilization"""
        alerts = []
        risk_util = state.get('risk_utilization', 0)
        threshold = self.alert_thresholds.get('risk_utilization_pct', 70)

        if risk_util >= threshold:
            alerts.append({
                'severity': 'warning',
                'message': f'Risk utilization at {risk_util:.1f}%',
                'metric': 'risk',
                'value': risk_util
            })

        return alerts

    def _check_position_health(self, state: TradingState) -> List[Dict[str, Any]]:
        """Check position health"""
        return []  # TODO: Implement position-specific checks

    def _check_system_health(self, state: TradingState) -> List[Dict[str, Any]]:
        """Check system health"""
        alerts = []
        system_health = state.get('system_health', {})

        if system_health.get('status') != 'healthy':
            alerts.append({
                'severity': 'critical',
                'message': 'System health degraded',
                'metric': 'system_health',
                'value': system_health.get('status')
            })

        return alerts

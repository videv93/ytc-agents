"""
Economic Calendar Agent (Agent 04)
Monitors economic news events and filters high-impact releases
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
import structlog
from agents.base import BaseAgent, TradingState

logger = structlog.get_logger()


class EconomicCalendarAgent(BaseAgent):
    """
    Economic Calendar Agent
    - Monitors upcoming economic news events
    - Filters high-impact releases
    - Implements trading restrictions around news
    - Provides alerts for upcoming events
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.news_api_url = config.get('agent_config', {}).get('economic_calendar', {}).get('news_api_url', '')
        self.filter_high_impact = config.get('agent_config', {}).get('economic_calendar', {}).get('filter_high_impact', True)
        self.stop_before_minutes = config.get('agent_config', {}).get('economic_calendar', {}).get('stop_trading_minutes_before', 5)
        self.resume_after_minutes = config.get('agent_config', {}).get('economic_calendar', {}).get('resume_trading_minutes_after', 5)

    async def _execute_logic(self, state: TradingState) -> Dict[str, Any]:
        """
        Check economic calendar for upcoming news events.

        Args:
            state: Current trading state

        Returns:
            Economic calendar analysis
        """
        self.logger.info("checking_economic_calendar",
                        instrument=state['instrument'])

        try:
            # Fetch upcoming news events
            upcoming_events = await self._fetch_news_events(
                instrument=state['instrument'],
                hours_ahead=24
            )

            # Filter high-impact events
            high_impact_events = [
                event for event in upcoming_events
                if event['impact'] == 'high'
            ] if self.filter_high_impact else upcoming_events

            # Check if trading should be restricted now
            restriction = self._check_trading_restriction(high_impact_events)

            # Get next critical event
            next_event = self._get_next_critical_event(high_impact_events)

            result = {
                'status': 'success',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'upcoming_events': high_impact_events[:10],  # Next 10 events
                'total_events': len(upcoming_events),
                'high_impact_count': len(high_impact_events),
                'trading_restricted': restriction['restricted'],
                'restriction_reason': restriction.get('reason'),
                'restriction_until': restriction.get('until'),
                'next_critical_event': next_event
            }

            # Add alert if trading is restricted
            if restriction['restricted']:
                state = self.add_alert(
                    state,
                    'warning',
                    f"Trading restricted: {restriction['reason']}"
                )

            self.logger.info("economic_calendar_checked",
                           high_impact_events=len(high_impact_events),
                           trading_restricted=restriction['restricted'])

            return result

        except Exception as e:
            self.logger.error("economic_calendar_check_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'trading_restricted': False  # Default to allow trading on error
            }

    async def _fetch_news_events(
        self,
        instrument: str,
        hours_ahead: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Fetch upcoming economic news events.

        Args:
            instrument: Trading instrument
            hours_ahead: Hours to look ahead

        Returns:
            List of news events
        """
        # TODO: Integrate with actual economic calendar API
        # Options: ForexFactory, Investing.com, Trading Economics, etc.

        self.logger.debug("fetching_news_events",
                         instrument=instrument,
                         hours_ahead=hours_ahead)

        # Mock data - replace with actual API call
        # Example events for GBP/USD
        now = datetime.now(timezone.utc)

        mock_events = [
            {
                'time': (now + timedelta(hours=2)).isoformat(),
                'currency': 'GBP',
                'event': 'Bank of England Interest Rate Decision',
                'impact': 'high',
                'forecast': '5.25%',
                'previous': '5.25%'
            },
            {
                'time': (now + timedelta(hours=6)).isoformat(),
                'currency': 'USD',
                'event': 'Non-Farm Payrolls',
                'impact': 'high',
                'forecast': '180K',
                'previous': '199K'
            },
            {
                'time': (now + timedelta(hours=12)).isoformat(),
                'currency': 'GBP',
                'event': 'GDP Growth Rate',
                'impact': 'medium',
                'forecast': '0.2%',
                'previous': '0.1%'
            }
        ]

        # Filter relevant events for the instrument
        if 'GBP' in instrument or 'USD' in instrument:
            return mock_events

        return []

    def _check_trading_restriction(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check if trading should be restricted based on upcoming news.

        Args:
            events: List of upcoming events

        Returns:
            Restriction status
        """
        now = datetime.now(timezone.utc)

        for event in events:
            event_time = datetime.fromisoformat(event['time'])
            minutes_until = (event_time - now).total_seconds() / 60

            # Check if we're in the restriction window
            if -self.resume_after_minutes <= minutes_until <= self.stop_before_minutes:
                restriction_until = event_time + timedelta(minutes=self.resume_after_minutes)

                return {
                    'restricted': True,
                    'reason': f"High-impact event: {event['event']}",
                    'event': event,
                    'until': restriction_until.isoformat(),
                    'minutes_until_event': minutes_until
                }

        return {
            'restricted': False
        }

    def _get_next_critical_event(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get the next critical news event.

        Args:
            events: List of events

        Returns:
            Next critical event or None
        """
        if not events:
            return None

        now = datetime.now(timezone.utc)

        # Sort by time
        future_events = [
            e for e in events
            if datetime.fromisoformat(e['time']) > now
        ]

        if not future_events:
            return None

        # Get nearest future event
        next_event = min(
            future_events,
            key=lambda e: datetime.fromisoformat(e['time'])
        )

        event_time = datetime.fromisoformat(next_event['time'])
        minutes_until = (event_time - now).total_seconds() / 60

        return {
            **next_event,
            'minutes_until': int(minutes_until)
        }

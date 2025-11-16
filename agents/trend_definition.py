"""
Trend Definition Agent (Agent 05)
Defines the trend on the trading timeframe (3min)
"""

from typing import Dict, Any
from datetime import datetime, timezone
import structlog
from agents.base import BaseAgent, TradingState
from skills.pivot_detection import PivotDetectionSkill

logger = structlog.get_logger()


class TrendDefinitionAgent(BaseAgent):
    """
    Trend Definition Agent
    - Analyzes 3min (trading) timeframe for trend
    - Identifies higher highs/higher lows or lower highs/lower lows
    - Tracks leading swing violations
    - Distinguishes weakening from reversing
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.swing_bars = config.get('agent_config', {}).get('trend_definition', {}).get('swing_bars', 3)
        self.confirmation_bars = config.get('agent_config', {}).get('trend_definition', {}).get('confirmation_bars', 2)
        self.min_strength = config.get('agent_config', {}).get('trend_definition', {}).get('min_trend_strength', 60)

        self.pivot_skill = PivotDetectionSkill(min_bars=self.swing_bars)

    async def _execute_logic(self, state: TradingState) -> Dict[str, Any]:
        """
        Define trend on trading timeframe.

        Args:
            state: Current trading state

        Returns:
            Trend definition results
        """
        self.logger.info("defining_trend",
                        instrument=state['instrument'])

        try:
            # Get trading timeframe data (3min)
            ohlc_data = await self._fetch_trading_tf_data(
                state['instrument'],
                timeframe='3min',
                bars=100
            )

            # Get current price
            current_price = float(ohlc_data.iloc[-1]['close'])

            # Detect swing points
            swing_points = self.pivot_skill.detect_swing_points(
                ohlc_data,
                swing_bars=self.swing_bars
            )

            # Classify trend
            trend_classification = self.pivot_skill.classify_trend(
                swing_points['swing_highs'],
                swing_points['swing_lows']
            )

            # Check for structure break
            structure_break = self.pivot_skill.identify_structure_break(
                current_price,
                trend_classification['trend'],
                swing_points['swing_highs'],
                swing_points['swing_lows']
            )

            # Determine trend state
            trend_state = self._determine_trend_state(
                trend_classification,
                structure_break,
                swing_points
            )

            # Identify leading swings
            leading_swings = self._identify_leading_swings(
                swing_points,
                trend_classification['trend']
            )

            result = {
                'status': 'success',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'timeframe': '3min',
                'current_price': current_price,
                'trend': trend_classification['trend'],
                'trend_confidence': trend_classification['confidence'],
                'trend_reason': trend_classification['reason'],
                'trend_state': trend_state,
                'structure_break': structure_break,
                'leading_swings': leading_swings,
                'swing_points': {
                    'recent_highs': swing_points['swing_highs'][-5:],
                    'recent_lows': swing_points['swing_lows'][-5:]
                }
            }

            # Update state
            state['trend'] = result

            self.logger.info("trend_defined",
                           trend=trend_classification['trend'],
                           confidence=trend_classification['confidence'],
                           state=trend_state)

            return result

        except Exception as e:
            self.logger.error("trend_definition_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    async def _fetch_trading_tf_data(
        self,
        instrument: str,
        timeframe: str,
        bars: int
    ) -> Any:
        """
        Fetch trading timeframe OHLC data.

        Args:
            instrument: Trading instrument
            timeframe: Timeframe
            bars: Number of bars

        Returns:
            DataFrame with OHLC data
        """
        import pandas as pd
        from datetime import timedelta

        # TODO: Replace with actual data fetch from Hummingbot Gateway
        dates = [datetime.now(timezone.utc) - timedelta(minutes=3*i) for i in range(bars, 0, -1)]

        # Get current price from gateway API
        base_price = 1.25  # Default fallback
        if self.gateway_client:
            try:
                market_data = await self.gateway_client.get_market_data(
                    connector=self.config.get('connector', 'oanda'),
                    trading_pair=instrument
                )
                if market_data.get('status') == 'ok':
                    base_price = market_data['price']
            except Exception as e:
                self.logger.warning("failed_to_fetch_price", error=str(e), using_default=base_price)

        data = {
            'timestamp': dates,
            'open': [base_price + (i * 0.00005) for i in range(bars)],
            'high': [base_price + (i * 0.00005) + 0.0002 for i in range(bars)],
            'low': [base_price + (i * 0.00005) - 0.0002 for i in range(bars)],
            'close': [base_price + (i * 0.00005) + 0.0001 for i in range(bars)]
        }

        return pd.DataFrame(data)

    def _determine_trend_state(
        self,
        trend: Dict[str, Any],
        structure_break: Dict[str, Any],
        swing_points: Dict[str, Any]
    ) -> str:
        """
        Determine the state of the trend.

        States:
        - strong: Clear trend with no violations
        - weakening: Structure break but trend intact
        - reversing: Leading swing violated
        - ranging: No clear trend

        Args:
            trend: Trend classification
            structure_break: Structure break analysis
            swing_points: Swing points

        Returns:
            Trend state
        """
        if trend['trend'] == 'ranging':
            return 'ranging'

        if structure_break['structure_broken']:
            # Check if it's just weakening or actually reversing
            if self._is_leading_swing_violated(swing_points, trend['trend']):
                return 'reversing'
            else:
                return 'weakening'

        # No structure break - strong trend
        if trend['confidence'] >= 80:
            return 'strong'
        else:
            return 'developing'

    def _is_leading_swing_violated(
        self,
        swing_points: Dict[str, Any],
        trend: str
    ) -> bool:
        """
        Check if the leading swing has been violated.

        YTC Rule: Leading swing violation = trend reversal

        Args:
            swing_points: Swing points
            trend: Current trend

        Returns:
            True if leading swing violated
        """
        if trend == 'uptrend' and len(swing_points['swing_highs']) >= 2:
            # In uptrend, leading swing is the last higher high
            # Violation = new high fails to exceed it
            last_two_highs = swing_points['swing_highs'][-2:]
            if last_two_highs[1]['price'] < last_two_highs[0]['price']:
                return True

        elif trend == 'downtrend' and len(swing_points['swing_lows']) >= 2:
            # In downtrend, leading swing is the last lower low
            # Violation = new low fails to exceed it
            last_two_lows = swing_points['swing_lows'][-2:]
            if last_two_lows[1]['price'] > last_two_lows[0]['price']:
                return True

        return False

    def _identify_leading_swings(
        self,
        swing_points: Dict[str, Any],
        trend: str
    ) -> Dict[str, Any]:
        """
        Identify the leading swings for the current trend.

        Args:
            swing_points: Swing points
            trend: Current trend

        Returns:
            Leading swing information
        """
        if trend == 'uptrend' and swing_points['swing_highs']:
            return {
                'leading_high': swing_points['swing_highs'][-1],
                'supporting_low': swing_points['swing_lows'][-1] if swing_points['swing_lows'] else None
            }
        elif trend == 'downtrend' and swing_points['swing_lows']:
            return {
                'leading_low': swing_points['swing_lows'][-1],
                'supporting_high': swing_points['swing_highs'][-1] if swing_points['swing_highs'] else None
            }
        else:
            return {}

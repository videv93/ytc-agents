"""
Market Structure Agent (Agent 03)
Analyzes higher timeframe market structure, identifies support/resistance zones
"""

from typing import Dict, Any, List
from datetime import datetime
import structlog
from agents.base import BaseAgent, TradingState
from skills.pivot_detection import PivotDetectionSkill

logger = structlog.get_logger()


class MarketStructureAgent(BaseAgent):
    """
    Market Structure Agent
    - Analyzes 30min (higher) timeframe for market structure
    - Identifies swing highs and lows
    - Marks support and resistance zones
    - Classifies overall structure quality
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.lookback_bars = config.get('agent_config', {}).get('market_structure', {}).get('lookback_bars', 100)
        self.swing_bars = config.get('agent_config', {}).get('market_structure', {}).get('swing_bars', 3)
        self.zone_tolerance = config.get('agent_config', {}).get('market_structure', {}).get('zone_tolerance_pct', 0.1) / 100

        # Initialize pivot detection skill
        self.pivot_skill = PivotDetectionSkill(min_bars=self.swing_bars)

    async def _execute_logic(self, state: TradingState) -> Dict[str, Any]:
        """
        Execute market structure analysis on higher timeframe.

        Args:
            state: Current trading state

        Returns:
            Market structure analysis results
        """
        self.logger.info("analyzing_market_structure",
                        instrument=state['instrument'])

        try:
            # Get higher timeframe OHLC data (30min)
            ohlc_data = await self._fetch_higher_tf_data(
                state['instrument'],
                timeframe='30min',
                bars=self.lookback_bars
            )

            # Detect swing points
            swing_points = self.pivot_skill.detect_swing_points(
                ohlc_data,
                swing_bars=self.swing_bars
            )

            # Identify support zones from swing lows
            support_zones = self.pivot_skill.find_support_resistance_zones(
                swing_points['swing_lows'],
                zone_tolerance=self.zone_tolerance
            )

            # Identify resistance zones from swing highs
            resistance_zones = self.pivot_skill.find_support_resistance_zones(
                swing_points['swing_highs'],
                zone_tolerance=self.zone_tolerance
            )

            # Classify overall trend from structure
            trend_classification = self.pivot_skill.classify_trend(
                swing_points['swing_highs'],
                swing_points['swing_lows']
            )

            # Calculate structure quality
            structure_quality = self._calculate_structure_quality(
                swing_points,
                support_zones,
                resistance_zones,
                trend_classification
            )

            # Build result
            result = {
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat(),
                'timeframe': '30min',
                'swing_points': {
                    'swing_highs': swing_points['swing_highs'][-10:],  # Last 10
                    'swing_lows': swing_points['swing_lows'][-10:],
                    'total_highs': len(swing_points['swing_highs']),
                    'total_lows': len(swing_points['swing_lows'])
                },
                'support_zones': support_zones[:5],  # Top 5 strongest
                'resistance_zones': resistance_zones[:5],
                'trend': trend_classification,
                'structure_quality': structure_quality,
                'key_levels': self._identify_key_levels(support_zones, resistance_zones)
            }

            # Update state
            state['market_structure'] = result

            self.logger.info("market_structure_complete",
                           support_zones=len(support_zones),
                           resistance_zones=len(resistance_zones),
                           trend=trend_classification['trend'],
                           quality=structure_quality)

            return result

        except Exception as e:
            self.logger.error("market_structure_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    async def _fetch_higher_tf_data(
        self,
        instrument: str,
        timeframe: str,
        bars: int
    ) -> Any:
        """
        Fetch OHLC data for higher timeframe.

        Args:
            instrument: Trading instrument
            timeframe: Timeframe (e.g., '30min')
            bars: Number of bars to fetch

        Returns:
            DataFrame with OHLC data
        """
        # TODO: Implement actual data fetching via Hummingbot API or data provider
        # For now, return mock data structure
        import pandas as pd
        from datetime import timedelta

        self.logger.debug("fetching_ohlc_data",
                         instrument=instrument,
                         timeframe=timeframe,
                         bars=bars)

        # Mock data - replace with actual API call
        dates = [datetime.utcnow() - timedelta(minutes=30*i) for i in range(bars, 0, -1)]

        # Generate realistic looking price data
        base_price = 1.2500
        data = {
            'timestamp': dates,
            'open': [base_price + (i * 0.0001) for i in range(bars)],
            'high': [base_price + (i * 0.0001) + 0.0005 for i in range(bars)],
            'low': [base_price + (i * 0.0001) - 0.0005 for i in range(bars)],
            'close': [base_price + (i * 0.0001) + 0.0002 for i in range(bars)]
        }

        return pd.DataFrame(data)

    def _calculate_structure_quality(
        self,
        swing_points: Dict[str, List],
        support_zones: List[Dict],
        resistance_zones: List[Dict],
        trend: Dict[str, Any]
    ) -> int:
        """
        Calculate overall structure quality score (0-100).

        Args:
            swing_points: Detected swing points
            support_zones: Support zones
            resistance_zones: Resistance zones
            trend: Trend classification

        Returns:
            Quality score 0-100
        """
        score = 0

        # Well-defined swing points (max 30 points)
        total_swings = len(swing_points['swing_highs']) + len(swing_points['swing_lows'])
        if total_swings >= 10:
            score += 30
        elif total_swings >= 5:
            score += 20
        else:
            score += 10

        # Clear support/resistance zones (max 30 points)
        strong_zones = len([z for z in support_zones + resistance_zones if z['strength'] >= 75])
        if strong_zones >= 3:
            score += 30
        elif strong_zones >= 2:
            score += 20
        else:
            score += 10

        # Clear trend (max 40 points)
        if trend['trend'] in ['uptrend', 'downtrend']:
            score += trend['confidence'] * 0.4
        else:
            score += 20  # Ranging is okay, just less clear

        return min(100, int(score))

    def _identify_key_levels(
        self,
        support_zones: List[Dict],
        resistance_zones: List[Dict]
    ) -> Dict[str, Any]:
        """
        Identify the most important key levels.

        Args:
            support_zones: All support zones
            resistance_zones: All resistance zones

        Returns:
            Key levels summary
        """
        key_levels = {
            'nearest_support': None,
            'nearest_resistance': None,
            'major_support': None,
            'major_resistance': None
        }

        if support_zones:
            # Nearest is first (closest to current price)
            key_levels['nearest_support'] = support_zones[0]['price_level']
            # Major is strongest
            major_support = max(support_zones, key=lambda x: x['strength'])
            key_levels['major_support'] = major_support['price_level']

        if resistance_zones:
            key_levels['nearest_resistance'] = resistance_zones[0]['price_level']
            major_resistance = max(resistance_zones, key=lambda x: x['strength'])
            key_levels['major_resistance'] = major_resistance['price_level']

        return key_levels

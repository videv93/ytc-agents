"""
Pivot Detection Skill
YTC swing point detection for market structure analysis
"""

from typing import Dict, List, Any
import pandas as pd
import numpy as np
import structlog

logger = structlog.get_logger()


class PivotDetectionSkill:
    """
    YTC Swing Point Detection Skill
    Identifies higher highs, lower lows, and swing points
    """

    def __init__(self, min_bars: int = 3):
        """
        Initialize pivot detection skill.

        Args:
            min_bars: Minimum bars on each side for swing point validation
        """
        self.min_bars = min_bars
        self.logger = logger.bind(skill="pivot_detection")

    def detect_swing_points(
        self,
        ohlc_data: pd.DataFrame,
        swing_bars: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify swing highs and lows per YTC methodology.

        A swing high requires:
        - Current bar high > N bars to left AND right

        A swing low requires:
        - Current bar low < N bars to left AND right

        Args:
            ohlc_data: DataFrame with columns: timestamp, open, high, low, close
            swing_bars: Number of bars on each side to validate swing

        Returns:
            Dictionary with swing_highs and swing_lows arrays
        """
        self.logger.info("detecting_swing_points",
                        bars=len(ohlc_data),
                        swing_bars=swing_bars)

        swing_highs = []
        swing_lows = []

        # Need at least swing_bars * 2 + 1 bars
        if len(ohlc_data) < (swing_bars * 2 + 1):
            self.logger.warning("insufficient_data", required=swing_bars * 2 + 1)
            return {'swing_highs': [], 'swing_lows': []}

        # Iterate through potential swing points
        for i in range(swing_bars, len(ohlc_data) - swing_bars):

            # Check for swing high
            current_high = ohlc_data.iloc[i]['high']
            is_swing_high = True

            for j in range(1, swing_bars + 1):
                left_high = ohlc_data.iloc[i - j]['high']
                right_high = ohlc_data.iloc[i + j]['high']

                if left_high >= current_high or right_high >= current_high:
                    is_swing_high = False
                    break

            if is_swing_high:
                swing_highs.append({
                    'index': i,
                    'price': float(current_high),
                    'timestamp': ohlc_data.iloc[i]['timestamp'].isoformat() if isinstance(
                        ohlc_data.iloc[i]['timestamp'], pd.Timestamp
                    ) else str(ohlc_data.iloc[i]['timestamp']),
                    'bar_count': swing_bars
                })

            # Check for swing low
            current_low = ohlc_data.iloc[i]['low']
            is_swing_low = True

            for j in range(1, swing_bars + 1):
                left_low = ohlc_data.iloc[i - j]['low']
                right_low = ohlc_data.iloc[i + j]['low']

                if left_low <= current_low or right_low <= current_low:
                    is_swing_low = False
                    break

            if is_swing_low:
                swing_lows.append({
                    'index': i,
                    'price': float(current_low),
                    'timestamp': ohlc_data.iloc[i]['timestamp'].isoformat() if isinstance(
                        ohlc_data.iloc[i]['timestamp'], pd.Timestamp
                    ) else str(ohlc_data.iloc[i]['timestamp']),
                    'bar_count': swing_bars
                })

        self.logger.info("swing_points_detected",
                        swing_highs=len(swing_highs),
                        swing_lows=len(swing_lows))

        return {
            'swing_highs': swing_highs,
            'swing_lows': swing_lows
        }

    def classify_trend(
        self,
        swing_highs: List[Dict],
        swing_lows: List[Dict]
    ) -> Dict[str, Any]:
        """
        Classify trend based on swing points.

        YTC Trend Rules:
        - Uptrend: Higher Highs + Higher Lows
        - Downtrend: Lower Highs + Lower Lows
        - Ranging: Mixed signals

        Args:
            swing_highs: List of swing high points
            swing_lows: List of swing low points

        Returns:
            Trend classification
        """
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {
                'trend': 'unknown',
                'reason': 'Insufficient swing points',
                'confidence': 0
            }

        # Check recent swing highs (last 3)
        recent_highs = swing_highs[-3:] if len(swing_highs) >= 3 else swing_highs
        higher_highs = all(
            recent_highs[i]['price'] > recent_highs[i-1]['price']
            for i in range(1, len(recent_highs))
        )

        # Check recent swing lows (last 3)
        recent_lows = swing_lows[-3:] if len(swing_lows) >= 3 else swing_lows
        higher_lows = all(
            recent_lows[i]['price'] > recent_lows[i-1]['price']
            for i in range(1, len(recent_lows))
        )

        lower_highs = all(
            recent_highs[i]['price'] < recent_highs[i-1]['price']
            for i in range(1, len(recent_highs))
        )

        lower_lows = all(
            recent_lows[i]['price'] < recent_lows[i-1]['price']
            for i in range(1, len(recent_lows))
        )

        # Determine trend
        if higher_highs and higher_lows:
            return {
                'trend': 'uptrend',
                'reason': 'Higher highs and higher lows',
                'confidence': 85,
                'last_high': recent_highs[-1]['price'],
                'last_low': recent_lows[-1]['price']
            }
        elif lower_highs and lower_lows:
            return {
                'trend': 'downtrend',
                'reason': 'Lower highs and lower lows',
                'confidence': 85,
                'last_high': recent_highs[-1]['price'],
                'last_low': recent_lows[-1]['price']
            }
        else:
            return {
                'trend': 'ranging',
                'reason': 'Mixed swing point pattern',
                'confidence': 60,
                'last_high': recent_highs[-1]['price'],
                'last_low': recent_lows[-1]['price']
            }

    def find_support_resistance_zones(
        self,
        swing_points: List[Dict],
        zone_tolerance: float = 0.001
    ) -> List[Dict[str, Any]]:
        """
        Identify support/resistance zones from swing points.

        Groups nearby swing points into zones.

        Args:
            swing_points: List of swing high or low points
            zone_tolerance: Price tolerance for grouping (as decimal, e.g., 0.001 = 0.1%)

        Returns:
            List of support/resistance zones
        """
        if not swing_points:
            return []

        zones = []
        used_points = set()

        for i, point in enumerate(swing_points):
            if i in used_points:
                continue

            price = point['price']
            zone_points = [point]
            used_points.add(i)

            # Find nearby points
            for j, other_point in enumerate(swing_points):
                if j in used_points:
                    continue

                other_price = other_point['price']
                price_diff_pct = abs(other_price - price) / price

                if price_diff_pct <= zone_tolerance:
                    zone_points.append(other_point)
                    used_points.add(j)

            # Create zone if we have at least 2 touches
            if len(zone_points) >= 2:
                prices = [p['price'] for p in zone_points]
                zones.append({
                    'price_level': float(np.mean(prices)),
                    'price_high': float(max(prices)),
                    'price_low': float(min(prices)),
                    'touches': len(zone_points),
                    'first_touch': zone_points[0]['timestamp'],
                    'last_touch': zone_points[-1]['timestamp'],
                    'strength': min(100, len(zone_points) * 25)  # Max 100
                })

        # Sort by strength
        zones.sort(key=lambda x: x['strength'], reverse=True)

        self.logger.info("zones_identified", zone_count=len(zones))

        return zones

    def identify_structure_break(
        self,
        current_price: float,
        trend: str,
        swing_highs: List[Dict],
        swing_lows: List[Dict]
    ) -> Dict[str, Any]:
        """
        Identify if price has broken market structure.

        YTC Rules:
        - In uptrend: break below last higher low = structure break
        - In downtrend: break above last lower high = structure break

        Args:
            current_price: Current market price
            trend: Current trend (uptrend, downtrend, ranging)
            swing_highs: List of swing highs
            swing_lows: List of swing lows

        Returns:
            Structure break analysis
        """
        if trend == 'uptrend' and swing_lows:
            last_higher_low = swing_lows[-1]['price']
            if current_price < last_higher_low:
                return {
                    'structure_broken': True,
                    'direction': 'bearish',
                    'level_broken': last_higher_low,
                    'current_price': current_price,
                    'severity': abs(current_price - last_higher_low) / last_higher_low * 100
                }

        elif trend == 'downtrend' and swing_highs:
            last_lower_high = swing_highs[-1]['price']
            if current_price > last_lower_high:
                return {
                    'structure_broken': True,
                    'direction': 'bullish',
                    'level_broken': last_lower_high,
                    'current_price': current_price,
                    'severity': abs(current_price - last_lower_high) / last_lower_high * 100
                }

        return {
            'structure_broken': False,
            'current_price': current_price
        }

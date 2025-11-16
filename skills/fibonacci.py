"""
Fibonacci Calculation Skill
YTC Fibonacci retracement and extension calculations
"""

from typing import Dict, List, Any
import structlog

logger = structlog.get_logger()


class FibonacciSkill:
    """
    Fibonacci calculation skill for YTC trading
    Calculates retracement and extension levels
    """

    # YTC standard Fibonacci levels
    RETRACEMENT_LEVELS = [0.236, 0.382, 0.500, 0.618, 0.786]
    EXTENSION_LEVELS = [1.272, 1.414, 1.618, 2.000, 2.618]

    def __init__(self):
        self.logger = logger.bind(skill="fibonacci")

    def calculate_retracements(
        self,
        swing_high: float,
        swing_low: float,
        direction: str = 'bullish'
    ) -> Dict[str, Any]:
        """
        Calculate Fibonacci retracement levels.

        For bullish retracements (upward swing):
        - Calculate from swing_low to swing_high
        - Retracements are below swing_high

        For bearish retracements (downward swing):
        - Calculate from swing_high to swing_low
        - Retracements are above swing_low

        Args:
            swing_high: High point of the swing
            swing_low: Low point of the swing
            direction: 'bullish' or 'bearish'

        Returns:
            Dictionary with retracement levels
        """
        self.logger.info("calculating_retracements",
                        swing_high=swing_high,
                        swing_low=swing_low,
                        direction=direction)

        swing_range = swing_high - swing_low
        levels = {}

        if direction == 'bullish':
            # Retracements from high back down
            for level in self.RETRACEMENT_LEVELS:
                price = swing_high - (swing_range * level)
                levels[f'fib_{int(level*100)}'] = round(price, 5)

        else:  # bearish
            # Retracements from low back up
            for level in self.RETRACEMENT_LEVELS:
                price = swing_low + (swing_range * level)
                levels[f'fib_{int(level*100)}'] = round(price, 5)

        return {
            'swing_high': swing_high,
            'swing_low': swing_low,
            'swing_range': swing_range,
            'direction': direction,
            'levels': levels,
            'key_levels': {
                '50%': levels['fib_50'],
                '61.8%': levels['fib_61']
            }
        }

    def calculate_extensions(
        self,
        swing_high: float,
        swing_low: float,
        direction: str = 'bullish'
    ) -> Dict[str, Any]:
        """
        Calculate Fibonacci extension levels for price targets.

        Args:
            swing_high: High point of the swing
            swing_low: Low point of the swing
            direction: 'bullish' or 'bearish'

        Returns:
            Dictionary with extension levels
        """
        self.logger.info("calculating_extensions",
                        swing_high=swing_high,
                        swing_low=swing_low,
                        direction=direction)

        swing_range = swing_high - swing_low
        levels = {}

        if direction == 'bullish':
            # Extensions above swing_high
            for level in self.EXTENSION_LEVELS:
                price = swing_high + (swing_range * (level - 1))
                levels[f'ext_{int(level*100)}'] = round(price, 5)

        else:  # bearish
            # Extensions below swing_low
            for level in self.EXTENSION_LEVELS:
                price = swing_low - (swing_range * (level - 1))
                levels[f'ext_{int(level*100)}'] = round(price, 5)

        return {
            'swing_high': swing_high,
            'swing_low': swing_low,
            'swing_range': swing_range,
            'direction': direction,
            'levels': levels,
            'key_targets': {
                'T1 (127.2%)': levels['ext_127'],
                'T2 (161.8%)': levels['ext_161']
            }
        }

    def find_nearest_fib_level(
        self,
        current_price: float,
        fib_levels: Dict[str, float],
        tolerance_pct: float = 0.5
    ) -> Dict[str, Any]:
        """
        Find nearest Fibonacci level to current price.

        Args:
            current_price: Current market price
            fib_levels: Dictionary of Fibonacci levels
            tolerance_pct: Tolerance percentage (0.5 = 0.5%)

        Returns:
            Nearest level information
        """
        nearest_level = None
        nearest_distance = float('inf')
        nearest_name = None

        for name, price in fib_levels.items():
            distance = abs(current_price - price)
            distance_pct = (distance / current_price) * 100

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_level = price
                nearest_name = name

        distance_pct = (nearest_distance / current_price) * 100
        is_near = distance_pct <= tolerance_pct

        return {
            'nearest_level': nearest_level,
            'level_name': nearest_name,
            'distance': nearest_distance,
            'distance_pct': distance_pct,
            'is_near_level': is_near,
            'current_price': current_price
        }

    def calculate_pullback_entry(
        self,
        trend_swing_high: float,
        trend_swing_low: float,
        direction: str = 'bullish',
        preferred_levels: List[float] = [0.50, 0.618]
    ) -> List[Dict[str, Any]]:
        """
        Calculate YTC pullback entry zones.

        YTC methodology: Look for pullbacks to 50% or 61.8%

        Args:
            trend_swing_high: High of trend swing
            trend_swing_low: Low of trend swing
            direction: Trend direction
            preferred_levels: Preferred Fibonacci entry levels

        Returns:
            List of entry zones
        """
        retracements = self.calculate_retracements(
            trend_swing_high,
            trend_swing_low,
            direction
        )

        entry_zones = []

        for level_pct in preferred_levels:
            level_key = f'fib_{int(level_pct*100)}'

            if level_key in retracements['levels']:
                price = retracements['levels'][level_key]

                entry_zones.append({
                    'level': f'{int(level_pct*100)}%',
                    'price': price,
                    'direction': direction,
                    'quality': 'high' if level_pct in [0.50, 0.618] else 'medium'
                })

        return entry_zones

"""
Setup Scanner Agent (Agent 07)
Scans for YTC trading setups (pullbacks and 3-swing traps)
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import structlog
from agents.base import BaseAgent, TradingState
from skills.fibonacci import FibonacciSkill

logger = structlog.get_logger()


class SetupScannerAgent(BaseAgent):
    """
    Setup Scanner Agent
    - Scans for pullback setups to structure
    - Identifies 3-swing trap patterns
    - Scores setup quality based on confluence
    - Filters by minimum quality threshold
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.min_score = config.get('agent_config', {}).get('setup_scanner', {}).get('min_score', 70)
        self.enabled_patterns = config.get('agent_config', {}).get('setup_scanner', {}).get('enabled_patterns', ['pullback', '3_swing_trap'])

        self.fib_skill = FibonacciSkill()

    async def _execute_logic(self, state: TradingState) -> Dict[str, Any]:
        """
        Scan for trading setups.

        Args:
            state: Current trading state

        Returns:
            Setup scanner results
        """
        self.logger.info("scanning_for_setups")

        try:
            # Get prerequisite data
            trend_data = state.get('trend', {})
            market_structure = state.get('market_structure', {})

            if not trend_data or trend_data.get('status') != 'success':
                return {
                    'status': 'error',
                    'error': 'Trend data not available',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

            setups_found = []

            # Scan for pullback setups
            if 'pullback' in self.enabled_patterns:
                pullback_setups = await self._scan_pullback_setups(
                    state,
                    trend_data,
                    market_structure
                )
                setups_found.extend(pullback_setups)

            # Scan for 3-swing trap
            if '3_swing_trap' in self.enabled_patterns:
                trap_setups = await self._scan_3swing_traps(
                    state,
                    trend_data
                )
                setups_found.extend(trap_setups)

            # Filter by minimum score
            high_quality_setups = [
                setup for setup in setups_found
                if setup['quality_score'] >= self.min_score
            ]

            # Sort by quality score
            high_quality_setups.sort(key=lambda x: x['quality_score'], reverse=True)

            result = {
                'status': 'success',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'setups_found': len(setups_found),
                'high_quality_setups': len(high_quality_setups),
                'setups': high_quality_setups,
                'min_score_threshold': self.min_score
            }

            self.logger.info("setup_scan_complete",
                           total_setups=len(setups_found),
                           high_quality=len(high_quality_setups))

            return result

        except Exception as e:
            self.logger.error("setup_scan_failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    async def _scan_pullback_setups(
        self,
        state: TradingState,
        trend_data: Dict[str, Any],
        market_structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Scan for pullback setups.

        YTC Pullback Setup:
        - Clear trend
        - Pullback to 50% or 61.8% Fibonacci
        - Pullback to support/resistance zone
        - Confluence of levels

        Args:
            state: Trading state
            trend_data: Trend analysis
            market_structure: Market structure data

        Returns:
            List of pullback setups
        """
        setups = []
        trend = trend_data['trend']

        if trend == 'ranging':
            return setups  # No pullback setups in ranging market

        # Get recent swing points
        swing_points = trend_data.get('swing_points', {})
        if not swing_points:
            return setups

        # Calculate Fibonacci levels from last major swing
        if trend == 'uptrend':
            recent_highs = swing_points.get('recent_highs', [])
            recent_lows = swing_points.get('recent_lows', [])

            if len(recent_highs) >= 1 and len(recent_lows) >= 1:
                swing_high = recent_highs[-1]['price']
                swing_low = recent_lows[-1]['price']

                # Calculate Fibonacci retracements
                fib_levels = self.fib_skill.calculate_retracements(
                    swing_high,
                    swing_low,
                    'bullish'
                )

                # Check if current price near Fib level
                # Get current price from gateway API
                current_price = 1.25  # Default fallback
                if self.gateway_client:
                    try:
                        market_data = await self.gateway_client.get_market_data(
                            connector=self.config.get('connector', 'oanda'),
                            trading_pair=state['instrument']
                        )
                        if market_data.get('status') == 'ok':
                            current_price = market_data['price']
                            self.logger.debug("fetched_current_price", price=current_price)
                    except Exception as e:
                        self.logger.warning("failed_to_fetch_price", error=str(e), using_default=current_price)

                nearest_fib = self.fib_skill.find_nearest_fib_level(
                    current_price,
                    fib_levels['levels'],
                    tolerance_pct=0.5
                )

                if nearest_fib['is_near_level']:
                    # Score the setup
                    quality_score = self._score_pullback_setup(
                        fib_levels,
                        nearest_fib,
                        market_structure,
                        trend_data
                    )

                    setups.append({
                        'type': 'pullback',
                        'direction': 'long',
                        'entry_zone': nearest_fib['nearest_level'],
                        'fib_level': nearest_fib['level_name'],
                        'swing_high': swing_high,
                        'swing_low': swing_low,
                        'quality_score': quality_score,
                        'confluence_factors': self._identify_confluence(
                            nearest_fib['nearest_level'],
                            market_structure,
                            'support'
                        )
                    })

        return setups

    async def _scan_3swing_traps(
        self,
        state: TradingState,
        trend_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Scan for 3-swing trap patterns.

        YTC 3-Swing Trap:
        - 3 swings forming a pattern
        - Trap against the trend
        - Breakout in trend direction

        Args:
            state: Trading state
            trend_data: Trend analysis

        Returns:
            List of 3-swing trap setups
        """
        setups = []

        # TODO: Implement 3-swing trap detection
        # This requires analyzing the last 3 swing points for the pattern

        return setups

    def _score_pullback_setup(
        self,
        fib_levels: Dict[str, Any],
        nearest_fib: Dict[str, Any],
        market_structure: Dict[str, Any],
        trend_data: Dict[str, Any]
    ) -> int:
        """
        Score a pullback setup based on quality factors.

        Args:
            fib_levels: Fibonacci levels
            nearest_fib: Nearest Fib level analysis
            market_structure: Market structure
            trend_data: Trend data

        Returns:
            Quality score 0-100
        """
        score = 0

        # Fibonacci level quality (max 30 points)
        if '61' in nearest_fib['level_name']:  # 61.8% golden ratio
            score += 30
        elif '50' in nearest_fib['level_name']:  # 50% level
            score += 25
        elif '38' in nearest_fib['level_name']:  # 38.2% level
            score += 20

        # Trend strength (max 30 points)
        trend_confidence = trend_data.get('trend_confidence', 0)
        score += int(trend_confidence * 0.3)

        # Confluence with structure (max 40 points)
        confluence_count = len(self._identify_confluence(
            nearest_fib['nearest_level'],
            market_structure,
            'support'
        ))

        if confluence_count >= 2:
            score += 40
        elif confluence_count >= 1:
            score += 25

        return min(100, score)

    def _identify_confluence(
        self,
        price_level: float,
        market_structure: Dict[str, Any],
        zone_type: str
    ) -> List[str]:
        """
        Identify confluence factors at a price level.

        Args:
            price_level: Price level to check
            market_structure: Market structure data
            zone_type: 'support' or 'resistance'

        Returns:
            List of confluence factors
        """
        factors = []

        # Check for nearby support/resistance zones
        zones = market_structure.get(f'{zone_type}_zones', [])

        for zone in zones:
            zone_price = zone['price_level']
            distance_pct = abs(zone_price - price_level) / price_level * 100

            if distance_pct <= 0.1:  # Within 0.1%
                factors.append(f'{zone_type}_zone')
                if zone['strength'] >= 75:
                    factors.append('strong_zone')
                break

        # Add other confluence factors
        # - Previous day high/low
        # - Round numbers
        # - Gap levels
        # etc.

        return factors

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
        Scan for all 5 YTC trading setups.

        YTC Setups:
        1. TST (Test of Support/Resistance) - Test of S/R expected to hold
        2. BOF (Breakout Failure) - Breakout that reverses
        3. BPB (Breakout Pullback) - Breakout that holds then pulls back
        4. PB (Simple Pullback) - Single-leg pullback within trend
        5. CPB (Complex Pullback) - Multi-swing pullback within trend

        Args:
            state: Current trading state

        Returns:
            Setup scanner results
        """
        self.logger.info("scanning_for_ytc_setups")

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

            # Scan for all 5 YTC setups
            # 1. TST - Test of Support/Resistance
            tst_setups = await self._scan_tst_setups(
                state,
                trend_data,
                market_structure
            )
            setups_found.extend(tst_setups)

            # 2. BOF - Breakout Failure
            bof_setups = await self._scan_bof_setups(
                state,
                trend_data,
                market_structure
            )
            setups_found.extend(bof_setups)

            # 3. BPB - Breakout Pullback
            bpb_setups = await self._scan_bpb_setups(
                state,
                trend_data,
                market_structure
            )
            setups_found.extend(bpb_setups)

            # 4. PB - Simple Pullback
            pb_setups = await self._scan_simple_pullback_setups(
                state,
                trend_data,
                market_structure
            )
            setups_found.extend(pb_setups)

            # 5. CPB - Complex Pullback
            cpb_setups = await self._scan_complex_pullback_setups(
                state,
                trend_data,
                market_structure
            )
            setups_found.extend(cpb_setups)

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

    async def _scan_tst_setups(
        self,
        state: TradingState,
        trend_data: Dict[str, Any],
        market_structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Scan for TST (Test of Support/Resistance) setups.

        TST Setup:
        - Price tests an area of S/R expected to hold
        - Can be higher timeframe S/R, range S/R, or swing H/L
        - Weakness on test identifies fading opportunity
        - Trade against the test direction

        Args:
            state: Trading state
            trend_data: Trend analysis
            market_structure: Market structure data

        Returns:
            List of TST setups
        """
        setups = []
        current_price = await self._get_current_price(state)

        # Check for tests of resistance zones (bearish TST - long opportunity)
        resistance_zones = market_structure.get('resistance_zones', [])
        for zone in resistance_zones:
            if self._is_price_near_level(current_price, zone['price_level'], tolerance_pct=0.3):
                quality_score = self._score_tst_setup(
                    zone,
                    market_structure,
                    trend_data,
                    'resistance'
                )
                if quality_score >= self.min_score:
                    setups.append({
                        'type': 'TST',
                        'direction': 'long',
                        'entry_zone': zone['price_level'],
                        'zone_type': 'resistance',
                        'zone_strength': zone.get('strength', 50),
                        'quality_score': quality_score,
                        'confluence_factors': self._identify_confluence(
                            zone['price_level'],
                            market_structure,
                            'resistance'
                        )
                    })

        # Check for tests of support zones (bullish TST - short opportunity)
        support_zones = market_structure.get('support_zones', [])
        for zone in support_zones:
            if self._is_price_near_level(current_price, zone['price_level'], tolerance_pct=0.3):
                quality_score = self._score_tst_setup(
                    zone,
                    market_structure,
                    trend_data,
                    'support'
                )
                if quality_score >= self.min_score:
                    setups.append({
                        'type': 'TST',
                        'direction': 'short',
                        'entry_zone': zone['price_level'],
                        'zone_type': 'support',
                        'zone_strength': zone.get('strength', 50),
                        'quality_score': quality_score,
                        'confluence_factors': self._identify_confluence(
                            zone['price_level'],
                            market_structure,
                            'support'
                        )
                    })

        return setups

    async def _scan_bof_setups(
        self,
        state: TradingState,
        trend_data: Dict[str, Any],
        market_structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Scan for BOF (Breakout Failure) setups.

        BOF Setup:
        - Price breaches S/R level with momentum
        - Breakout shows weakness (closes near the level)
        - Reversal expected back through S/R
        - Trade in direction opposite to breakout

        Args:
            state: Trading state
            trend_data: Trend analysis
            market_structure: Market structure data

        Returns:
            List of BOF setups
        """
        setups = []
        current_price = await self._get_current_price(state)
        candles = state.get('candles', [])

        if len(candles) < 2:
            return setups

        # Check for failed breakouts above resistance
        resistance_zones = market_structure.get('resistance_zones', [])
        for zone in resistance_zones:
            # Check if price broke above but is showing weakness
            if current_price > zone['price_level']:
                last_candle = candles[-1]
                # BOF: Close near open (weak breakout) suggests reversal
                candle_range = last_candle.get('high', current_price) - last_candle.get('low', current_price)
                if candle_range > 0:
                    close_location = (last_candle.get('close', current_price) - last_candle.get('low', current_price)) / candle_range
                    if close_location < 0.4:  # Weakness indicator
                        quality_score = self._score_bof_setup(
                            zone, market_structure, trend_data, 'resistance'
                        )
                        if quality_score >= self.min_score:
                            setups.append({
                                'type': 'BOF',
                                'direction': 'short',
                                'entry_zone': zone['price_level'],
                                'breakout_level': zone['price_level'],
                                'zone_strength': zone.get('strength', 50),
                                'quality_score': quality_score,
                                'confluence_factors': self._identify_confluence(
                                    zone['price_level'],
                                    market_structure,
                                    'resistance'
                                )
                            })

        # Check for failed breakouts below support
        support_zones = market_structure.get('support_zones', [])
        for zone in support_zones:
            if current_price < zone['price_level']:
                last_candle = candles[-1]
                candle_range = last_candle.get('high', current_price) - last_candle.get('low', current_price)
                if candle_range > 0:
                    close_location = (last_candle.get('high', current_price) - last_candle.get('close', current_price)) / candle_range
                    if close_location < 0.4:  # Weakness indicator
                        quality_score = self._score_bof_setup(
                            zone, market_structure, trend_data, 'support'
                        )
                        if quality_score >= self.min_score:
                            setups.append({
                                'type': 'BOF',
                                'direction': 'long',
                                'entry_zone': zone['price_level'],
                                'breakout_level': zone['price_level'],
                                'zone_strength': zone.get('strength', 50),
                                'quality_score': quality_score,
                                'confluence_factors': self._identify_confluence(
                                    zone['price_level'],
                                    market_structure,
                                    'support'
                                )
                            })

        return setups

    async def _scan_bpb_setups(
        self,
        state: TradingState,
        trend_data: Dict[str, Any],
        market_structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Scan for BPB (Breakout Pullback) setups.

        BPB Setup:
        - Price breaches S/R with strength
        - Pullback to the breakout level or nearby
        - Price shows strength post-breakout before pullback
        - Trade in direction of breakout on pullback

        Args:
            state: Trading state
            trend_data: Trend analysis
            market_structure: Market structure data

        Returns:
            List of BPB setups
        """
        setups = []
        current_price = await self._get_current_price(state)
        candles = state.get('candles', [])

        if len(candles) < 3:
            return setups

        # Check for strong breakouts above resistance
        resistance_zones = market_structure.get('resistance_zones', [])
        for zone in resistance_zones:
            if current_price > zone['price_level']:
                last_candle = candles[-1]
                prev_candle = candles[-2] if len(candles) >= 2 else None
                
                # Check for strength in breakout candle
                candle_range = last_candle.get('high', current_price) - last_candle.get('low', current_price)
                if candle_range > 0:
                    close_location = (last_candle.get('close', current_price) - last_candle.get('low', current_price)) / candle_range
                    if close_location > 0.6:  # Strength indicator
                        quality_score = self._score_bpb_setup(
                            zone, market_structure, trend_data, 'resistance'
                        )
                        if quality_score >= self.min_score:
                            setups.append({
                                'type': 'BPB',
                                'direction': 'long',
                                'entry_zone': zone['price_level'],
                                'breakout_level': zone['price_level'],
                                'zone_strength': zone.get('strength', 50),
                                'quality_score': quality_score,
                                'confluence_factors': self._identify_confluence(
                                    zone['price_level'],
                                    market_structure,
                                    'resistance'
                                )
                            })

        # Check for strong breakouts below support
        support_zones = market_structure.get('support_zones', [])
        for zone in support_zones:
            if current_price < zone['price_level']:
                last_candle = candles[-1]
                candle_range = last_candle.get('high', current_price) - last_candle.get('low', current_price)
                if candle_range > 0:
                    close_location = (last_candle.get('high', current_price) - last_candle.get('close', current_price)) / candle_range
                    if close_location > 0.6:  # Strength indicator
                        quality_score = self._score_bpb_setup(
                            zone, market_structure, trend_data, 'support'
                        )
                        if quality_score >= self.min_score:
                            setups.append({
                                'type': 'BPB',
                                'direction': 'short',
                                'entry_zone': zone['price_level'],
                                'breakout_level': zone['price_level'],
                                'zone_strength': zone.get('strength', 50),
                                'quality_score': quality_score,
                                'confluence_factors': self._identify_confluence(
                                    zone['price_level'],
                                    market_structure,
                                    'support'
                                )
                            })

        return setups

    async def _scan_simple_pullback_setups(
        self,
        state: TradingState,
        trend_data: Dict[str, Any],
        market_structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Scan for PB (Simple Pullback) setups.

        PB Setup:
        - Single-leg pullback within a clear trend
        - Pullback to swing low (uptrend) or swing high (downtrend)
        - Fibonacci levels (50%, 61.8%)
        - Weakness on pullback indicates reversal to trend

        Args:
            state: Trading state
            trend_data: Trend analysis
            market_structure: Market structure data

        Returns:
            List of simple pullback setups
        """
        setups = []
        trend = trend_data.get('trend')
        current_price = await self._get_current_price(state)

        if trend not in ['uptrend', 'downtrend']:
            return setups

        swing_points = trend_data.get('swing_points', {})
        if not swing_points:
            return setups

        if trend == 'uptrend':
            recent_highs = swing_points.get('recent_highs', [])
            recent_lows = swing_points.get('recent_lows', [])

            if len(recent_highs) >= 1 and len(recent_lows) >= 1:
                swing_high = recent_highs[-1]['price']
                swing_low = recent_lows[-1]['price']

                fib_levels = self.fib_skill.calculate_retracements(
                    swing_high,
                    swing_low,
                    'bullish'
                )

                nearest_fib = self.fib_skill.find_nearest_fib_level(
                    current_price,
                    fib_levels['levels'],
                    tolerance_pct=0.5
                )

                if nearest_fib['is_near_level']:
                    quality_score = self._score_pullback_setup(
                        fib_levels,
                        nearest_fib,
                        market_structure,
                        trend_data
                    )
                    if quality_score >= self.min_score:
                        setups.append({
                            'type': 'PB',
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

        elif trend == 'downtrend':
            recent_highs = swing_points.get('recent_highs', [])
            recent_lows = swing_points.get('recent_lows', [])

            if len(recent_highs) >= 1 and len(recent_lows) >= 1:
                swing_high = recent_highs[-1]['price']
                swing_low = recent_lows[-1]['price']

                fib_levels = self.fib_skill.calculate_retracements(
                    swing_high,
                    swing_low,
                    'bearish'
                )

                nearest_fib = self.fib_skill.find_nearest_fib_level(
                    current_price,
                    fib_levels['levels'],
                    tolerance_pct=0.5
                )

                if nearest_fib['is_near_level']:
                    quality_score = self._score_pullback_setup(
                        fib_levels,
                        nearest_fib,
                        market_structure,
                        trend_data
                    )
                    if quality_score >= self.min_score:
                        setups.append({
                            'type': 'PB',
                            'direction': 'short',
                            'entry_zone': nearest_fib['nearest_level'],
                            'fib_level': nearest_fib['level_name'],
                            'swing_high': swing_high,
                            'swing_low': swing_low,
                            'quality_score': quality_score,
                            'confluence_factors': self._identify_confluence(
                                nearest_fib['nearest_level'],
                                market_structure,
                                'resistance'
                            )
                        })

        return setups

    async def _scan_complex_pullback_setups(
        self,
        state: TradingState,
        trend_data: Dict[str, Any],
        market_structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Scan for CPB (Complex Pullback) setups.

        CPB Setup:
        - Multi-swing or extended-duration pullback within trend
        - Multiple legs with trapped traders
        - Stronger setup than simple pullback
        - Often traps reversal traders at deep retracements

        Args:
            state: Trading state
            trend_data: Trend analysis
            market_structure: Market structure data

        Returns:
            List of complex pullback setups
        """
        setups = []
        trend = trend_data.get('trend')
        current_price = await self._get_current_price(state)
        candles = state.get('candles', [])

        if trend not in ['uptrend', 'downtrend'] or len(candles) < 5:
            return setups

        swing_points = trend_data.get('swing_points', {})
        if not swing_points:
            return setups

        # CPB is characterized by deeper retracements (38.2%, 50%, 61.8%)
        # with multiple swings suggesting trapped traders

        if trend == 'uptrend':
            recent_highs = swing_points.get('recent_highs', [])
            recent_lows = swing_points.get('recent_lows', [])

            if len(recent_highs) >= 2 and len(recent_lows) >= 2:
                swing_high = recent_highs[-1]['price']
                swing_low = recent_lows[-1]['price']

                fib_levels = self.fib_skill.calculate_retracements(
                    swing_high,
                    swing_low,
                    'bullish'
                )

                # Check for price in deeper retracement zones (38-62%)
                for level in fib_levels.get('levels', []):
                    if 35 <= level['percentage'] <= 65:
                        if self._is_price_near_level(current_price, level['price'], tolerance_pct=0.5):
                            # Check for multiple swings (complex pattern)
                            num_lows = len(recent_lows)
                            if num_lows >= 2:  # At least 2 lows = multiple legs
                                quality_score = self._score_complex_pullback(
                                    fib_levels,
                                    level,
                                    market_structure,
                                    trend_data,
                                    num_lows
                                )
                                if quality_score >= self.min_score:
                                    setups.append({
                                        'type': 'CPB',
                                        'direction': 'long',
                                        'entry_zone': level['price'],
                                        'fib_level': f"{level['percentage']:.1f}%",
                                        'swing_high': swing_high,
                                        'swing_low': swing_low,
                                        'num_swing_legs': num_lows,
                                        'quality_score': quality_score,
                                        'confluence_factors': self._identify_confluence(
                                            level['price'],
                                            market_structure,
                                            'support'
                                        )
                                    })

        elif trend == 'downtrend':
            recent_highs = swing_points.get('recent_highs', [])
            recent_lows = swing_points.get('recent_lows', [])

            if len(recent_highs) >= 2 and len(recent_lows) >= 2:
                swing_high = recent_highs[-1]['price']
                swing_low = recent_lows[-1]['price']

                fib_levels = self.fib_skill.calculate_retracements(
                    swing_high,
                    swing_low,
                    'bearish'
                )

                # Check for price in deeper retracement zones
                for level in fib_levels.get('levels', []):
                    if 35 <= level['percentage'] <= 65:
                        if self._is_price_near_level(current_price, level['price'], tolerance_pct=0.5):
                            num_highs = len(recent_highs)
                            if num_highs >= 2:  # At least 2 highs = multiple legs
                                quality_score = self._score_complex_pullback(
                                    fib_levels,
                                    level,
                                    market_structure,
                                    trend_data,
                                    num_highs
                                )
                                if quality_score >= self.min_score:
                                    setups.append({
                                        'type': 'CPB',
                                        'direction': 'short',
                                        'entry_zone': level['price'],
                                        'fib_level': f"{level['percentage']:.1f}%",
                                        'swing_high': swing_high,
                                        'swing_low': swing_low,
                                        'num_swing_legs': num_highs,
                                        'quality_score': quality_score,
                                        'confluence_factors': self._identify_confluence(
                                            level['price'],
                                            market_structure,
                                            'resistance'
                                        )
                                    })

        return setups

    async def _get_current_price(self, state: TradingState) -> float:
        """
        Get current market price.

        Args:
            state: Trading state

        Returns:
            Current price
        """
        # Try to get from latest candle
        candles = state.get('candles', [])
        if candles:
            return candles[-1].get('close', 3000.0)

        # Try to fetch from gateway
        if self.gateway_client:
            try:
                market_data = await self.gateway_client.get_market_data(
                    connector=self.config.get('connector', 'binance-perpetual-testnet'),
                    trading_pair=state.get('instrument', 'eth-usdt')
                )
                if market_data.get('status') == 'ok':
                    return market_data['price']
            except Exception as e:
                self.logger.warning("failed_to_fetch_price", error=str(e))

        return 3000.0  # Default fallback for ETH-USDT

    def _is_price_near_level(
        self,
        current_price: float,
        level_price: float,
        tolerance_pct: float = 0.5
    ) -> bool:
        """
        Check if current price is near a specific level.

        Args:
            current_price: Current market price
            level_price: Level to check against
            tolerance_pct: Tolerance percentage (default 0.5%)

        Returns:
            True if price is near level, False otherwise
        """
        distance = abs(current_price - level_price) / level_price * 100
        return distance <= tolerance_pct

    def _score_tst_setup(
        self,
        zone: Dict[str, Any],
        market_structure: Dict[str, Any],
        trend_data: Dict[str, Any],
        zone_type: str
    ) -> int:
        """
        Score a TST (Test of Support/Resistance) setup.

        Args:
            zone: S/R zone being tested
            market_structure: Market structure
            trend_data: Trend data
            zone_type: 'support' or 'resistance'

        Returns:
            Quality score 0-100
        """
        score = 0

        # Zone strength (max 40 points)
        zone_strength = zone.get('strength', 50)
        score += int((zone_strength / 100) * 40)

        # Trend alignment (max 30 points)
        trend = trend_data.get('trend')
        if zone_type == 'resistance' and trend == 'downtrend':
            score += 30
        elif zone_type == 'support' and trend == 'uptrend':
            score += 30
        else:
            score += 15

        # Confluence factors (max 30 points)
        confluence_count = len(self._identify_confluence(
            zone['price_level'],
            market_structure,
            zone_type
        ))
        if confluence_count >= 2:
            score += 30
        elif confluence_count >= 1:
            score += 20

        return min(100, score)

    def _score_bof_setup(
        self,
        zone: Dict[str, Any],
        market_structure: Dict[str, Any],
        trend_data: Dict[str, Any],
        zone_type: str
    ) -> int:
        """
        Score a BOF (Breakout Failure) setup.

        Args:
            zone: S/R zone
            market_structure: Market structure
            trend_data: Trend data
            zone_type: 'support' or 'resistance'

        Returns:
            Quality score 0-100
        """
        score = 0

        # Zone strength (max 35 points)
        zone_strength = zone.get('strength', 50)
        score += int((zone_strength / 100) * 35)

        # Failed breakout penalty (max 35 points)
        # Higher probability if zone is strong
        if zone_strength >= 75:
            score += 35
        elif zone_strength >= 60:
            score += 25
        else:
            score += 15

        # Confluence (max 30 points)
        confluence_count = len(self._identify_confluence(
            zone['price_level'],
            market_structure,
            zone_type
        ))
        if confluence_count >= 2:
            score += 30
        elif confluence_count >= 1:
            score += 20

        return min(100, score)

    def _score_bpb_setup(
        self,
        zone: Dict[str, Any],
        market_structure: Dict[str, Any],
        trend_data: Dict[str, Any],
        zone_type: str
    ) -> int:
        """
        Score a BPB (Breakout Pullback) setup.

        Args:
            zone: S/R zone
            market_structure: Market structure
            trend_data: Trend data
            zone_type: 'support' or 'resistance'

        Returns:
            Quality score 0-100
        """
        score = 0

        # Zone strength (max 35 points)
        zone_strength = zone.get('strength', 50)
        score += int((zone_strength / 100) * 35)

        # Successful breakout (max 35 points)
        # Higher probability if zone is strong
        if zone_strength >= 75:
            score += 35
        elif zone_strength >= 60:
            score += 28
        else:
            score += 18

        # Confluence (max 30 points)
        confluence_count = len(self._identify_confluence(
            zone['price_level'],
            market_structure,
            zone_type
        ))
        if confluence_count >= 2:
            score += 30
        elif confluence_count >= 1:
            score += 20

        return min(100, score)

    def _score_complex_pullback(
        self,
        fib_levels: Dict[str, Any],
        level: Dict[str, Any],
        market_structure: Dict[str, Any],
        trend_data: Dict[str, Any],
        num_swing_legs: int
    ) -> int:
        """
        Score a CPB (Complex Pullback) setup.

        Args:
            fib_levels: Fibonacci levels
            level: Current Fib level
            market_structure: Market structure
            trend_data: Trend data
            num_swing_legs: Number of swing legs in pullback

        Returns:
            Quality score 0-100
        """
        score = 0

        # Fibonacci level quality (max 25 points)
        percentage = level.get('percentage', 50)
        if 60 <= percentage <= 62:  # 61.8% golden ratio
            score += 25
        elif 48 <= percentage <= 52:  # 50% level
            score += 22
        elif 36 <= percentage <= 40:  # 38.2% level
            score += 18

        # Multiple swing complexity (max 35 points)
        if num_swing_legs >= 3:
            score += 35
        elif num_swing_legs >= 2:
            score += 25

        # Trend strength (max 30 points)
        trend_confidence = trend_data.get('trend_confidence', 0)
        score += int(trend_confidence * 0.3)

        # Confluence (max 10 points)
        confluence_count = len(self._identify_confluence(
            level['price'],
            market_structure,
            'support' if trend_data.get('trend') == 'uptrend' else 'resistance'
        ))
        if confluence_count >= 2:
            score += 10

        return min(100, score)

    def _score_pullback_setup(
        self,
        fib_levels: Dict[str, Any],
        nearest_fib: Dict[str, Any],
        market_structure: Dict[str, Any],
        trend_data: Dict[str, Any]
    ) -> int:
        """
        Score a PB (Simple Pullback) setup based on quality factors.

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

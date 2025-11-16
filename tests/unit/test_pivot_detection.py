"""
Unit tests for Pivot Detection Skill
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from skills.pivot_detection import PivotDetectionSkill


@pytest.fixture
def pivot_skill():
    """Create pivot detection skill for testing"""
    return PivotDetectionSkill(min_bars=3)


@pytest.fixture
def uptrend_data():
     """Create sample uptrend OHLC data"""
     dates = [datetime.now() - timedelta(minutes=i) for i in range(100, 0, -1)]

     # Create uptrend data
     data = {
         'timestamp': dates,
         'open': [1.2000 + (i * 0.0001) for i in range(100)],
         'high': [1.2005 + (i * 0.0001) for i in range(100)],
         'low': [1.1995 + (i * 0.0001) for i in range(100)],
         'close': [1.2002 + (i * 0.0001) for i in range(100)]
     }

     return pd.DataFrame(data)


@pytest.fixture
def downtrend_data():
     """Create sample downtrend OHLC data"""
     dates = [datetime.now() - timedelta(minutes=i) for i in range(100, 0, -1)]

     # Create downtrend data
     data = {
         'timestamp': dates,
         'open': [1.2100 - (i * 0.0001) for i in range(100)],
         'high': [1.2105 - (i * 0.0001) for i in range(100)],
         'low': [1.2095 - (i * 0.0001) for i in range(100)],
         'close': [1.2102 - (i * 0.0001) for i in range(100)]
     }

     return pd.DataFrame(data)


class TestSwingPointDetection:
    """Test swing point detection"""

    def test_detect_swing_points_basic(self, pivot_skill, uptrend_data):
        """Test basic swing point detection"""
        result = pivot_skill.detect_swing_points(uptrend_data, swing_bars=3)

        assert 'swing_highs' in result
        assert 'swing_lows' in result
        assert isinstance(result['swing_highs'], list)
        assert isinstance(result['swing_lows'], list)

    def test_swing_points_have_required_fields(self, pivot_skill, uptrend_data):
        """Test that swing points have all required fields"""
        result = pivot_skill.detect_swing_points(uptrend_data, swing_bars=3)

        if result['swing_highs']:
            swing_high = result['swing_highs'][0]
            assert 'index' in swing_high
            assert 'price' in swing_high
            assert 'timestamp' in swing_high
            assert 'bar_count' in swing_high

    def test_insufficient_data_returns_empty(self, pivot_skill):
        """Test that insufficient data returns empty results"""
        small_data = pd.DataFrame({
            'timestamp': [datetime.now()],
            'open': [1.2000],
            'high': [1.2005],
            'low': [1.1995],
            'close': [1.2002]
        })

        result = pivot_skill.detect_swing_points(small_data, swing_bars=3)

        assert result['swing_highs'] == []
        assert result['swing_lows'] == []


class TestTrendClassification:
    """Test trend classification"""

    def test_uptrend_detection(self, pivot_skill, uptrend_data):
        """Test uptrend is correctly identified"""
        swing_points = pivot_skill.detect_swing_points(uptrend_data)

        # Manually create higher highs and higher lows
        swing_highs = [
            {'price': 1.2010, 'timestamp': '2024-01-01T10:00:00'},
            {'price': 1.2020, 'timestamp': '2024-01-01T10:10:00'},
            {'price': 1.2030, 'timestamp': '2024-01-01T10:20:00'}
        ]
        swing_lows = [
            {'price': 1.2000, 'timestamp': '2024-01-01T10:00:00'},
            {'price': 1.2010, 'timestamp': '2024-01-01T10:10:00'},
            {'price': 1.2020, 'timestamp': '2024-01-01T10:20:00'}
        ]

        result = pivot_skill.classify_trend(swing_highs, swing_lows)

        assert result['trend'] == 'uptrend'
        assert result['confidence'] > 0

    def test_downtrend_detection(self, pivot_skill):
        """Test downtrend is correctly identified"""
        swing_highs = [
            {'price': 1.2030, 'timestamp': '2024-01-01T10:00:00'},
            {'price': 1.2020, 'timestamp': '2024-01-01T10:10:00'},
            {'price': 1.2010, 'timestamp': '2024-01-01T10:20:00'}
        ]
        swing_lows = [
            {'price': 1.2020, 'timestamp': '2024-01-01T10:00:00'},
            {'price': 1.2010, 'timestamp': '2024-01-01T10:10:00'},
            {'price': 1.2000, 'timestamp': '2024-01-01T10:20:00'}
        ]

        result = pivot_skill.classify_trend(swing_highs, swing_lows)

        assert result['trend'] == 'downtrend'
        assert result['confidence'] > 0

    def test_insufficient_swings_returns_unknown(self, pivot_skill):
        """Test that insufficient swing points returns unknown"""
        result = pivot_skill.classify_trend(
            [{'price': 1.2000, 'timestamp': '2024-01-01T10:00:00'}],
            [{'price': 1.1990, 'timestamp': '2024-01-01T10:00:00'}]
        )

        assert result['trend'] == 'unknown'


class TestSupportResistanceZones:
    """Test support/resistance zone identification"""

    def test_zone_creation(self, pivot_skill):
        """Test that zones are created from nearby swing points"""
        swing_points = [
            {'price': 1.2000, 'timestamp': '2024-01-01T10:00:00'},
            {'price': 1.2001, 'timestamp': '2024-01-01T10:10:00'},
            {'price': 1.2002, 'timestamp': '2024-01-01T10:20:00'},
            {'price': 1.2050, 'timestamp': '2024-01-01T10:30:00'}
        ]

        zones = pivot_skill.find_support_resistance_zones(
            swing_points,
            zone_tolerance=0.001
        )

        # Should create at least one zone from the first 3 nearby points
        assert len(zones) >= 1

    def test_zone_strength_calculation(self, pivot_skill):
        """Test that zone strength is calculated correctly"""
        swing_points = [
            {'price': 1.2000, 'timestamp': '2024-01-01T10:00:00'},
            {'price': 1.2001, 'timestamp': '2024-01-01T10:10:00'}
        ]

        zones = pivot_skill.find_support_resistance_zones(swing_points)

        if zones:
            assert 'strength' in zones[0]
            assert zones[0]['strength'] > 0
            assert zones[0]['strength'] <= 100


class TestStructureBreak:
    """Test structure break identification"""

    def test_uptrend_structure_break(self, pivot_skill):
        """Test structure break in uptrend"""
        swing_lows = [
            {'price': 1.2010, 'timestamp': '2024-01-01T10:00:00'}
        ]

        result = pivot_skill.identify_structure_break(
            current_price=1.2005,  # Below last higher low
            trend='uptrend',
            swing_highs=[],
            swing_lows=swing_lows
        )

        assert result['structure_broken'] == True
        assert result['direction'] == 'bearish'

    def test_downtrend_structure_break(self, pivot_skill):
        """Test structure break in downtrend"""
        swing_highs = [
            {'price': 1.2010, 'timestamp': '2024-01-01T10:00:00'}
        ]

        result = pivot_skill.identify_structure_break(
            current_price=1.2015,  # Above last lower high
            trend='downtrend',
            swing_highs=swing_highs,
            swing_lows=[]
        )

        assert result['structure_broken'] == True
        assert result['direction'] == 'bullish'

    def test_no_structure_break(self, pivot_skill):
        """Test no structure break"""
        swing_lows = [
            {'price': 1.2010, 'timestamp': '2024-01-01T10:00:00'}
        ]

        result = pivot_skill.identify_structure_break(
            current_price=1.2015,  # Above last higher low (good)
            trend='uptrend',
            swing_highs=[],
            swing_lows=swing_lows
        )

        assert result['structure_broken'] == False

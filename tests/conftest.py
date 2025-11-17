"""
Pytest configuration and shared fixtures
"""

import pytest
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        'anthropic_api_key': 'test-api-key',
        'model': 'claude-sonnet-4-20250514',
        'session_config': {
            'market': 'crypto',
            'instrument': 'ETH-USDT',
            'session_start_time': '09:30:00',
            'duration_hours': 3
        },
        'risk_config': {
            'risk_per_trade_pct': 1.0,
            'max_session_risk_pct': 3.0,
            'max_positions': 3
        },
        'account_config': {
            'initial_balance': 100000.0
        }
    }

"""
BTC-USDT YTC Price Action Analysis
Analysis of recent 5-minute data to identify YTC setups
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Sample of recent candles (last 100 candles for analysis)
# This represents the last ~8 hours of price action

def identify_swing_points(df, lookback=5):
    """Identify swing highs and lows"""
    swing_highs = []
    swing_lows = []

    for i in range(lookback, len(df) - lookback):
        # Swing High: high is higher than lookback bars before and after
        if all(df['high'].iloc[i] > df['high'].iloc[i-j] for j in range(1, lookback+1)) and \
           all(df['high'].iloc[i] > df['high'].iloc[i+j] for j in range(1, lookback+1)):
            swing_highs.append({
                'index': i,
                'time': df['time'].iloc[i],
                'price': df['high'].iloc[i]
            })

        # Swing Low: low is lower than lookback bars before and after
        if all(df['low'].iloc[i] < df['low'].iloc[i-j] for j in range(1, lookback+1)) and \
           all(df['low'].iloc[i] < df['low'].iloc[i+j] for j in range(1, lookback+1)):
            swing_lows.append({
                'index': i,
                'time': df['time'].iloc[i],
                'price': df['low'].iloc[i]
            })

    return swing_highs, swing_lows

def identify_support_resistance(swing_highs, swing_lows, tolerance=100):
    """Cluster swing points into S/R zones"""
    levels = []

    # Combine all swing prices
    all_swings = [(sh['price'], 'H') for sh in swing_highs] + [(sl['price'], 'L') for sl in swing_lows]

    if not all_swings:
        return levels

    all_swings.sort(key=lambda x: x[0])

    # Cluster nearby levels
    current_cluster = [all_swings[0][0]]

    for price, swing_type in all_swings[1:]:
        if price - current_cluster[-1] <= tolerance:
            current_cluster.append(price)
        else:
            # Save cluster as S/R level
            avg_price = np.mean(current_cluster)
            levels.append({
                'price': avg_price,
                'touches': len(current_cluster),
                'strength': 'Strong' if len(current_cluster) >= 3 else 'Moderate'
            })
            current_cluster = [price]

    # Don't forget the last cluster
    if current_cluster:
        avg_price = np.mean(current_cluster)
        levels.append({
            'price': avg_price,
            'touches': len(current_cluster),
            'strength': 'Strong' if len(current_cluster) >= 3 else 'Moderate'
        })

    return levels

def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    high = df['high']
    low = df['low']
    close = df['close']

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()

    return atr.iloc[-1]

# Recent price action summary
recent_data = """
Key Observations from Last 24 Hours (5-min candles):

MAJOR SWING POINTS:
- Recent High: 96,600 (11/16 09:55 UTC)
- Recent Low: 92,994.60 (11/16 23:00 UTC)
- Current Price: 95,780.20

PRICE ACTION ZONES:
- Resistance Zone: 95,800 - 96,000 (current area)
- Support Zone: 94,850 - 95,000 (recent bounce area)
- Strong Support: 93,000 - 93,500 (tested overnight)

TREND ANALYSIS:
The market showed a clear downtrend from the 96,600 high, declining to test the 93,000
level overnight. Since then, we've seen a recovery rally back to the 95,700-95,800 zone.

Current Structure:
- Higher timeframe: Corrective/Choppy after decline from 96,600
- Recent bounce from 93,000 shows buying interest
- Now testing resistance at 95,800 area
- Making higher lows: 93,000 -> 94,850 -> current consolidation near 95,000

Volume Analysis:
- Heavy volume during the decline (15:50-18:00)
- Strong volume on bounce from 93,000 level
- Lower volume consolidation in recent hours (typical of Asian session)
"""

print(recent_data)

# YTC SETUP IDENTIFICATION
print("\n" + "="*80)
print("YTC PRICE ACTION SETUP ANALYSIS")
print("="*80)

current_price = 95780
atr_estimate = 350  # Approximate based on recent volatility

print(f"\nCurrent Price: ${current_price:,.2f}")
print(f"Estimated ATR (14): ${atr_estimate:,.2f}")

print("\n" + "-"*80)
print("IDENTIFIED YTC SETUPS:")
print("-"*80)

# Setup 1: Potential BPB (Breakout Pullback) if 95,800 breaks
print("\n1. POTENTIAL BPB (BREAKOUT PULLBACK) - LONG")
print("   Status: FORMING - Watching for breakout above 95,800 resistance")
print("   Conditions:")
print("   - Price consolidated near 95,000-95,400 zone (higher low structure)")
print("   - Currently testing 95,800 resistance (previous swing area)")
print("   - If breaks above 95,800 with momentum, wait for pullback")
print("   ")
print("   Entry Strategy:")
print("   - Wait for break and close above 95,850")
print("   - Enter on pullback to 95,600-95,700 (broken resistance becomes support)")
print("   - Entry Zone: 95,600 - 95,700")
print("   - Stop Loss: 95,350 (below pullback low)")
print("   - Target 1 (T1): 96,200 (2:1 R:R)")
print("   - Target 2 (T2): 96,600 (previous high, 3.3:1 R:R)")
print("   - Risk:Reward: 2:1 to 3.3:1")
print("   - Direction: LONG")

# Setup 2: TST at 95,000 support
print("\n2. TST (TEST OF SUPPORT) - LONG")
print("   Status: VALID if price pulls back to 95,000 zone")
print("   Conditions:")
print("   - 95,000 level held multiple times (established support)")
print("   - Recent higher low at 94,850")
print("   - Looking for test and hold at this zone")
print("   ")
print("   Entry Strategy:")
print("   - Wait for pullback to 94,950 - 95,050 zone")
print("   - Look for bullish price action (rejection wick, bullish engulf)")
print("   - Entry Zone: 94,950 - 95,050")
print("   - Stop Loss: 94,700 (below recent swing low)")
print("   - Target 1 (T1): 95,600 (2:1 R:R)")
print("   - Target 2 (T2): 96,000 (resistance zone, 3:1 R:R)")
print("   - Risk:Reward: 2:1 to 3:1")
print("   - Direction: LONG")

# Setup 3: BOF if fails at resistance
print("\n3. BOF (BREAKOUT FAILURE) - SHORT")
print("   Status: WATCHING - If 95,800-96,000 resistance holds and rejects")
print("   Conditions:")
print("   - Multiple tests of 95,800-96,000 zone")
print("   - If price breaks above briefly then fails back below")
print("   - Trapped longs provide fuel for reversal")
print("   ")
print("   Entry Strategy:")
print("   - If price spikes to 95,900-96,000 and quickly reverses")
print("   - Enter on break back below 95,700 with momentum")
print("   - Entry Zone: 95,650 - 95,700 (after failure confirmed)")
print("   - Stop Loss: 96,100 (above failed breakout high)")
print("   - Target 1 (T1): 95,000 (support zone, 1.6:1 R:R)")
print("   - Target 2 (T2): 94,500 (larger support, 2.9:1 R:R)")
print("   - Risk:Reward: 1.6:1 to 2.9:1")
print("   - Direction: SHORT")

print("\n" + "-"*80)
print("CURRENT MARKET BIAS:")
print("-"*80)
print("""
- TREND: Choppy/Corrective after decline from 96,600
- STRUCTURE: Making higher lows (93,000 -> 94,850 -> 95,000+)
- BIAS: Cautiously BULLISH if 95,000 holds; NEUTRAL at resistance
- KEY LEVEL: 95,800 is critical - break above is bullish, rejection is neutral/bearish

RECOMMENDED APPROACH:
1. BEST SETUP: Wait for BPB long if 95,800 breaks cleanly (highest probability)
2. ALTERNATIVE: TST long at 95,000 if pullback occurs with bullish confirmation
3. DEFENSIVE: BOF short only if clear rejection at 96,000 with volume

RISK MANAGEMENT:
- Position size for 1% account risk
- ATR stop distance: ~350 points suggests use structure-based stops
- Avoid trading during low liquidity periods
- Watch for higher timeframe alignment
""")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)

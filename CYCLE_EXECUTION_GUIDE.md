# YTC Trading System - Cycle Execution Guide

## Overview

The YTC trading system runs in **phases**, and within the **Active Trading Phase**, it executes **cycles** that repeat until the session ends. Each cycle performs setup scanning, entry execution, and trade management.

---

## 1. Workflow Phases

### Pre-Market Phase (Runs Once)
1. **System Init** (01) - Platform connectivity check
2. **Risk Management** (02) - Initialize risk parameters
3. **Market Structure** (03) - Identify S/R zones (30min)
4. **Economic Calendar** (04) - Check for news events
5. **Emergency Check** - Validate system health
6. **Logging & Audit** (17) - Record initialization
7. → **Transition to SESSION_OPEN**

### Session Open Phase (Runs Once)
1. **Trend Definition** (05) - Analyze trend (3min)
2. **Strength & Weakness** (06) - Momentum analysis
3. **Logging & Audit** (17) - Record analysis
4. → **Transition to ACTIVE_TRADING**

### Active Trading Phase (Runs in Cycles)
This phase loops until session end or emergency stop:

```
┌─────────────────────────────────────────────────────────┐
│                    CYCLE N                              │
├─────────────────────────────────────────────────────────┤
│ 1. Real-Time Monitoring (11) - Health check             │
│ 2. Setup Scanner (07) - Scan for setups [ONCE/CYCLE]    │
│    ├─ If already scanned this cycle: SKIP               │
│    └─ If not scanned: RUN & mark cycle_scanned          │
│ 3. Entry Execution (08) - Execute entries (every cycle) │
│ 4. Trade Management (09) - Manage positions             │
│ 5. Exit Execution (10) - Execute exits                  │
│ 6. Contingency Check (16) - Emergency monitoring        │
│ 7. Logging & Audit (17) - Record cycle data             │
│                                                         │
└─────────────────────────────────────────────────────────┘
         ↓ (if session not over)
    Go to Cycle N+1
```

### Post-Market Phase (Runs Once)
1. **Session Review** (12) - Analyze trades
2. **Performance Analytics** (13) - Calculate metrics
3. **Learning & Optimization** (14) - Extract patterns
4. **Next Session Prep** (15) - Plan next session
5. **Logging & Audit** (17) - Archive session
6. → **Transition to SHUTDOWN**

### Shutdown Phase
- Final cleanup
- Position closure if configured
- Session report generation
- System stop

---

## 2. Active Trading Cycle in Detail

### What Runs Once Per Cycle

**Setup Scanner (Agent 07)**
- Scans for all 5 YTC setup types:
  - TST (Test of Support/Resistance)
  - BOF (Breakout Failure)
  - BPB (Breakout Pullback)
  - PB (Simple Pullback)
  - CPB (Complex Pullback)
- Filters by quality score (min 70)
- Ranks setups by quality
- **Execution**: Only runs once per cycle due to `_should_run_setup_scanner()` routing

**How It Works:**
1. Orchestrator increments `_workflow_cycles` after logging
2. State is updated with `_workflow_cycle = current_cycle_number`
3. Setup Scanner executes and records `cycle_scanned = state['_workflow_cycle']`
4. Next cycle, routing function checks: `if cycle_scanned == current_cycle`
   - If YES: SKIP (already scanned this cycle)
   - If NO: RUN (new cycle, scan again)

### What Runs Every Cycle

**Real-Time Monitoring (Agent 11)**
- Checks system health
- Monitors broker connectivity
- Generates alerts
- Executes once per cycle

**Entry Execution (Agent 08)**
- Takes action on setup_scanner results
- Identifies entry triggers (LWP/HWP)
- Validates with risk management
- Places orders
- **Executes every cycle** (no cycle throttling)

**Trade Management (Agent 09)**
- Updates trailing stops
- Moves stops to breakeven at +1R
- Executes partial exits at T1
- Checks time-based exits
- **Executes if positions exist**

**Exit Execution (Agent 10)**
- Closes positions on targets
- Executes stop losses
- Handles time-based exits
- Records trade completion
- **Executes if needed**

**Contingency Management (Agent 16)**
- Continuously monitors for emergencies
- Checks session P&L limits (-3%)
- Monitors system health
- Executes emergency procedures if needed
- **Executes every cycle** (always watching)

**Logging & Audit (Agent 17)**
- Records all agent outputs
- Maintains audit trail
- Updates database with cycle data
- **Executes every cycle**

---

## 3. Cycle Routing Logic (Updated)

### Setup Scanner Routing

```python
def _should_run_setup_scanner(state) -> str:
    agent_outputs = state.get('agent_outputs', {})
    setup_scanner_output = agent_outputs.get('setup_scanner', {})
    
    # Check if already scanned in this cycle
    if setup_scanner_output and \
       setup_scanner_output.get('cycle_scanned') == orchestrator._workflow_cycles:
        return "skip"  # Already scanned, go to trade_management
    
    return "scan"  # New cycle, execute scan
```

### Workflow Edges (Active Trading)

```
monitoring ──→ setup_scanner ──conditional──┐
                                             ├─→ entry_execution ──→ trade_management ──conditional──┐
                                             │                                                        ├─→ exit_execution → logging
                                   (skip if   │                                                        │
                                   scanned)  └────────────────────────────────────────────────────────┘
                                             (manage if
                                              positions)
```

---

## 4. State Management in a Cycle

### TradingState Keys Used for Cycle Control

```python
state = {
    '_workflow_cycle': 1,        # Current cycle number (set by _after_logging_route)
    'phase': 'active_trading',   # Current phase
    'session_id': 'uuid-123',    # Session identifier
    
    # Agent outputs (persist across cycles)
    'agent_outputs': {
        'setup_scanner': {
            'status': 'success',
            'cycle_scanned': 1,        # Which cycle this scan was from
            'setups': [...],           # List of found setups
            'timestamp': '2025-11-17...'
        },
        'entry_execution': {
            'status': 'executed',
            'setup': {...},
            'order': {...}
        },
        ...
    },
    
    # Position tracking
    'positions': [...],                # Open positions
    'open_positions_count': 0,
    
    # Risk tracking
    'session_pnl': 0.0,
    'session_pnl_pct': 0.0,
    'emergency_stop': False
}
```

### Cycle Counter Increment

1. **Logging & Audit runs** (end of cycle)
2. **_after_logging_route is called**
3. **Increments `_workflow_cycles += 1`**
4. **Sets `state['_workflow_cycle'] = _workflow_cycles`**
5. **Routes back to monitoring** (unless session over)

---

## 5. Example: Cycle Execution Sequence

### Cycle 1 (FIRST ITERATION)

```
1. monitoring (11)
   → Checks health
   
2. setup_scanner (07)
   → cycle_scanned NOT in output yet
   → EXECUTES
   → Returns: cycle_scanned = 1, setups = [Setup1, Setup2, ...]
   
3. entry_execution (08)
   → EXECUTES every cycle
   → Checks if Setup1 is triggered
   → Entry not triggered yet
   → Returns: status='waiting'
   
4. trade_management (09)
   → No positions yet
   → SKIPS (no_open_positions)
   → Goes to exit_execution anyway
   
5. exit_execution (10)
   → No positions
   → Returns: no_action
   
6. logging_audit (17)
   → Records all outputs
   → Increments _workflow_cycles to 2
   → Routes back to monitoring
```

### Cycle 2 (SECOND ITERATION)

```
1. monitoring (11)
   → Checks health (running fine)
   
2. setup_scanner (07)
   → cycle_scanned = 1 (from previous cycle)
   → _workflow_cycles = 2 (current)
   → 1 ≠ 2, so CONDITION SKIPPED
   → Actually NO - it skips going INTO setup_scanner
   → Routes directly to entry_execution
   → Uses previous scan results (from Cycle 1)
   
3. entry_execution (08)
   → EXECUTES (no cycle limit)
   → Setup1 price now at entry zone
   → Entry is triggered!
   → Places order
   → Returns: status='executed', order_id='12345'
   
4. trade_management (09)
   → Position created from entry
   → Positions exist
   → EXECUTES
   → Sets initial trailing stop
   
5. exit_execution (10)
   → No exit needed yet
   
6. logging_audit (17)
   → Records cycle data
   → Increments _workflow_cycles to 3
   → Routes to monitoring
```

### Cycle 3 (THIRD ITERATION)

```
1. monitoring (11)
   → All systems normal
   
2. setup_scanner (07)
   → cycle_scanned = 1 (from Cycle 1)
   → _workflow_cycles = 3 (current)
   → 1 ≠ 3, so STILL SKIPPED
   → Routes to entry_execution
   → Previous setups still available
   
3. entry_execution (08)
   → EXECUTES
   → Setup1 already has position
   → No new entry
   → Returns: status='no_action'
   
4. trade_management (09)
   → Position from Cycle 2 exists
   → EXECUTES
   → Updates trailing stop
   → Checks for breakeven move (if +1R)
   → Returns: stop_updated = 1.25, position_management_complete
   
5. exit_execution (10)
   → No exit yet
   
6. logging_audit (17)
   → Increments to _workflow_cycles = 4
```

### Cycle N (AFTER MANY HOURS)

```
1. monitoring (11)
   → Checks - session end time reached
   
2-6. Agents execute normally
   
7. _after_logging_route
   → _workflow_cycles > 5 OR phase='shutdown'
   → Returns "end"
   → Workflow terminates
   → Transitions to POST_MARKET phase
```

---

## 6. Key Design Decisions

### Why Setup Scanner Runs Once Per Cycle

1. **Efficiency**: Scanning is CPU-intensive (Fibonacci calculations, pattern matching)
2. **Consistency**: Entry execution has 1 scan result per cycle to work with
3. **Realistic**: Markets update OHLC on each candle close, not multiple times per second
4. **Prevents Loop Locking**: Without throttling, setup_scanner → entry_execution could re-trigger

### Why Entry Execution Runs Every Cycle

1. **Responsiveness**: Entry triggers must be checked on every bar/tick
2. **Multiple Setups**: Different setups may have different triggers
3. **Dynamic Prices**: As price moves, new triggers may activate
4. **Risk Check**: Each execution validates against current risk limits

### Why Trade Management Runs When Positions Exist

1. **Efficiency**: No work needed if no positions
2. **Continuous Monitoring**: Active positions need real-time management
3. **Trailing Stops**: Must update on every bar
4. **Partial Exits**: Target levels must be checked each cycle

---

## 7. Implementation Summary

### Changes Made to Orchestrator

1. **Added `_should_run_setup_scanner()` method**
   - Checks if `cycle_scanned == current_cycle`
   - Returns "scan" or "skip"

2. **Updated workflow edges**
   - setup_scanner → conditional routing
   - Skip routes to entry_execution
   - Preserves previous scan results

3. **Set `state['_workflow_cycle']` in `_after_logging_route()`**
   - Increments before each cycle routing
   - Available to all agents

### Changes Made to Setup Scanner

1. **Added `cycle_scanned` to output**
   - Tracks which cycle the scan executed in
   - Used by orchestrator routing logic

---

## 8. Monitoring a Cycle

### Check Current Cycle Number
```python
state = orchestrator.get_state()
current_cycle = state.get('_workflow_cycle', 0)
print(f"Currently in cycle: {current_cycle}")
```

### Check if Setup Scanner Ran This Cycle
```python
setup_output = state['agent_outputs'].get('setup_scanner', {})
scan_cycle = setup_output.get('cycle_scanned')
current_cycle = state.get('_workflow_cycle')
if scan_cycle == current_cycle:
    print("Setup scanner just ran this cycle")
else:
    print(f"Setup scanner ran in cycle {scan_cycle}, using cached results")
```

### Check Setup Results
```python
setup_output = state['agent_outputs'].get('setup_scanner', {})
setups = setup_output.get('setups', [])
print(f"Available setups: {len(setups)}")
for setup in setups:
    print(f"  - {setup['type']} ({setup['direction']}) at {setup['entry_zone']}")
```

---

## Summary

The YTC system executes in **phases**, with the **Active Trading Phase** running repeated **cycles**:

- **Setup Scanner (Agent 07)**: Runs ONCE per cycle, results cached for entire cycle
- **Entry Execution (Agent 08)**: Runs EVERY cycle, acts on scanner results
- **Trade Management (Agent 09)**: Runs EVERY cycle if positions exist
- **All Other Agents**: Run per cycle based on their logic

This design balances **efficiency** (don't rescan constantly) with **responsiveness** (check every bar for entries/exits).

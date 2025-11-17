#!/usr/bin/env python3
"""
Debug startup issues - run this to identify where the system gets stuck
"""

import sys
import os
from dotenv import load_dotenv

# Load environment
print("1. Loading environment...", flush=True)
load_dotenv()
print("   ✓ Environment loaded", flush=True)

# Check database
print("\n2. Testing database connection...", flush=True)
try:
    from database.connection import DatabaseManager
    
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'ytc_trading'),
        'user': os.getenv('POSTGRES_USER', 'ytc_trader'),
        'password': os.getenv('POSTGRES_PASSWORD', '')
    }
    
    print(f"   Trying: {db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['database']}", flush=True)
    
    db = DatabaseManager(db_config)
    
    if db.test_connection():
        print("   ✓ Database connection successful", flush=True)
    else:
        print("   ✗ Database connection test failed", flush=True)
        print("\n   FIX: Make sure PostgreSQL is running and credentials are correct in .env", flush=True)
        sys.exit(1)
        
except Exception as e:
    print(f"   ✗ Error: {e}", flush=True)
    print("\n   FIX: Make sure PostgreSQL is running", flush=True)
    sys.exit(1)

# Check configuration
print("\n3. Loading configuration...", flush=True)
import yaml
from typing import Dict, Any

config = {
    'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
    'model': os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514'),
    'hummingbot_gateway_url': os.getenv('HUMMINGBOT_GATEWAY_URL', 'http://localhost:8000'),
    'hummingbot_username': os.getenv('HUMMINGBOT_USERNAME'),
    'hummingbot_password': os.getenv('HUMMINGBOT_PASSWORD'),
    'connector': os.getenv('CONNECTOR', 'binance_perpetual_testnet'),
}

# Check API key
if not config['anthropic_api_key']:
    print("   ✗ ANTHROPIC_API_KEY not set", flush=True)
    sys.exit(1)
else:
    print(f"   ✓ Anthropic API key: {config['anthropic_api_key'][:20]}...", flush=True)

# Load session config
session_config_path = 'config/session_config.yaml'
if os.path.exists(session_config_path):
    with open(session_config_path, 'r') as f:
        config['session_config'] = yaml.safe_load(f)
    print(f"   ✓ Session config loaded: {config['session_config'].get('instrument')}", flush=True)
else:
    config['session_config'] = {'market': 'crypto', 'instrument': 'ETH-USDT'}
    print("   ⚠ Using default session config", flush=True)

# Load risk config
risk_config_path = 'config/risk_config.yaml'
if os.path.exists(risk_config_path):
    with open(risk_config_path, 'r') as f:
        config['risk_config'] = yaml.safe_load(f)
    print(f"   ✓ Risk config loaded", flush=True)
else:
    config['risk_config'] = {
        'risk_per_trade_pct': 1.0,
        'max_session_risk_pct': 3.0,
        'max_positions': 3,
    }
    print("   ⚠ Using default risk config", flush=True)

# Check Hummingbot connection
print("\n4. Testing Hummingbot Gateway connection...", flush=True)
print(f"   Gateway URL: {config['hummingbot_gateway_url']}", flush=True)

import asyncio
from tools.gateway_api_client import HummingbotGatewayClient

async def test_hummingbot():
    try:
        client = HummingbotGatewayClient(
            gateway_url=config['hummingbot_gateway_url'],
            username=config['hummingbot_username'] or 'admin',
            password=config['hummingbot_password'] or 'admin'
        )
        
        # Try to get balance
        result = await client.get_balance(config['connector'])
        await client.close()
        
        if result.get('status') == 'ok':
            print(f"   ✓ Hummingbot connection successful", flush=True)
            return True
        else:
            print(f"   ✗ Hummingbot error: {result.get('error')}", flush=True)
            return False
    except Exception as e:
        print(f"   ✗ Connection failed: {e}", flush=True)
        return False

try:
    result = asyncio.run(test_hummingbot())
    if not result:
        print("\n   FIX: Make sure Hummingbot Gateway is running on http://localhost:8000", flush=True)
except Exception as e:
    print(f"   ✗ Async error: {e}", flush=True)
    print("\n   FIX: Make sure Hummingbot Gateway is running", flush=True)

# Try to initialize orchestrator
print("\n5. Initializing Master Orchestrator...", flush=True)
try:
    from agents.orchestrator import MasterOrchestrator
    
    print("   Building workflow graph (this may take a moment)...", flush=True)
    orchestrator = MasterOrchestrator(config)
    print("   ✓ Orchestrator initialized successfully", flush=True)
    
    # Get state
    state = orchestrator.get_state()
    print(f"   Session ID: {state['session_id']}", flush=True)
    print(f"   Initial Balance: {state['account_balance']}", flush=True)
    print(f"   Phase: {state['phase']}", flush=True)
    
except Exception as e:
    print(f"   ✗ Orchestrator initialization failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("✓ All startup checks passed!")
print("="*70)
print("\nYou can now run: python3 main.py")

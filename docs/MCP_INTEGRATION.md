# MCP Integration with Hummingbot

This document describes the Model Context Protocol (MCP) integration for Hummingbot trading operations in the YTC Agent System.

## Overview

The YTC trading system now uses **MCP (Model Context Protocol)** instead of direct HTTP API calls to interact with Hummingbot Gateway. This provides:

- **Standardized interface** for Claude agents to interact with trading platforms
- **Type-safe tool definitions** with input validation
- **Better error handling** and logging
- **Fallback mechanisms** for development and testing
- **Scalability** for adding new trading operations

## Architecture

```
┌─────────────────────────────────────────────────────┐
│             YTC Agent System                         │
│  ┌──────────────────────────────────────┐          │
│  │  Agents (System Init, Entry, Exit)   │          │
│  │  - Use BaseAgent MCP helper methods  │          │
│  └──────────────┬───────────────────────┘          │
│                 │                                    │
│  ┌──────────────▼───────────────────────┐          │
│  │  HummingbotMCPClient                 │          │
│  │  - Wraps Claude Tools API            │          │
│  │  - Provides trading tool interface   │          │
│  └──────────────┬───────────────────────┘          │
│                 │                                    │
│  ┌──────────────▼───────────────────────┐          │
│  │  Claude API (with Tools)             │          │
│  │  - Processes tool definitions        │          │
│  └──────────────┬───────────────────────┘          │
└─────────────────┼───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│  Optional: HummingbotMCPServer                      │
│  - Standalone MCP server (future enhancement)       │
│  - Direct HTTP → Hummingbot Gateway                 │
└─────────────────────────────────────────────────────┘
```

## Components

### 1. MCP Client (`tools/mcp_client.py`)

The `HummingbotMCPClient` class provides a high-level interface for agents to interact with Hummingbot:

```python
from tools.mcp_client import HummingbotMCPClient
from anthropic import Anthropic

# Initialize
client = Anthropic(api_key="your-key")
mcp_client = HummingbotMCPClient(client, model="claude-sonnet-4-20250514")

# Place order
result = await mcp_client.place_order(
    connector="oanda",
    trading_pair="GBP/USD",
    side="buy",
    amount=1.0,
    order_type="market"
)

# Get balance
balance = await mcp_client.get_balance(connector="oanda")

# Close position
close_result = await mcp_client.close_position(
    connector="oanda",
    trading_pair="GBP/USD"
)
```

### 2. MCP Server (`tools/hummingbot_mcp_server.py`)

A standalone MCP server that wraps Hummingbot Gateway API (optional, for future use):

```bash
# Run standalone
python -m tools.hummingbot_mcp_server

# Or with custom gateway URL
HUMMINGBOT_GATEWAY_URL=http://localhost:15888 python -m tools.hummingbot_mcp_server
```

### 3. BaseAgent Integration

All agents inherit MCP helper methods from `BaseAgent`:

```python
class MyAgent(BaseAgent):
    async def _execute_logic(self, state: TradingState):
        # Check gateway health
        status = await self.hb_check_gateway_status()

        # Get account balance
        balance = await self.hb_get_balance("oanda")

        # Place order
        order = await self.hb_place_order(
            connector="oanda",
            trading_pair="GBP/USD",
            side="buy",
            amount=1.0,
            order_type="market",
            price=1.2500
        )

        return {'status': 'success', 'order': order}
```

## Available Tools

The MCP integration provides 10 tools for trading operations:

### 1. `place_order`
Place a market or limit order.

**Parameters:**
- `connector` (string): Exchange connector (e.g., "oanda")
- `trading_pair` (string): Trading pair (e.g., "GBP/USD")
- `side` (string): "buy" or "sell"
- `amount` (number): Position size
- `order_type` (string): "market" or "limit"
- `price` (number, optional): Limit price
- `time_in_force` (string, optional): "GTC", "IOC", or "FOK"

**Example:**
```python
await agent.hb_place_order(
    connector="oanda",
    trading_pair="GBP/USD",
    side="buy",
    amount=1.0,
    order_type="limit",
    price=1.2500
)
```

### 2. `cancel_order`
Cancel an existing order.

**Parameters:**
- `connector` (string): Exchange connector
- `order_id` (string): Order ID to cancel
- `trading_pair` (string, optional): Trading pair

### 3. `get_balance`
Get account balance.

**Parameters:**
- `connector` (string): Exchange connector
- `currency` (string, optional): Specific currency

### 4. `get_positions`
Get open positions.

**Parameters:**
- `connector` (string): Exchange connector
- `trading_pair` (string, optional): Filter by trading pair

### 5. `get_market_data`
Get current market price and ticker data.

**Parameters:**
- `connector` (string): Exchange connector
- `trading_pair` (string): Trading pair

### 6. `get_order_status`
Get status of a specific order.

**Parameters:**
- `connector` (string): Exchange connector
- `order_id` (string): Order ID

### 7. `check_gateway_status`
Check if Hummingbot Gateway is healthy.

**Parameters:** None

### 8. `check_connector_status`
Check if a connector is available.

**Parameters:**
- `connector` (string): Connector name

### 9. `get_open_orders`
Get all open orders.

**Parameters:**
- `connector` (string): Exchange connector
- `trading_pair` (string, optional): Filter by pair

### 10. `close_position`
Close an open position.

**Parameters:**
- `connector` (string): Exchange connector
- `trading_pair` (string): Trading pair
- `amount` (number, optional): Amount to close (null = close all)

## Configuration

### MCP Configuration (`config/mcp_config.yaml`)

```yaml
mcp:
  enabled: true

  gateway:
    url: "http://localhost:15888"
    timeout_seconds: 30

  connector:
    name: "oanda"

  development:
    use_mock_fallback: true
    mock_delay_ms: 100
```

### Agent Configuration

Enable/disable MCP per agent:

```yaml
agents:
  system_init:
    mcp_enabled: true
    required_tools:
      - check_gateway_status
      - check_connector_status
      - get_balance

  entry_execution:
    mcp_enabled: true
    required_tools:
      - place_order
      - get_market_data
```

## Agent Updates

### SystemInitAgent

Updated to use MCP for:
- Gateway health check (`hb_check_gateway_status`)
- Connector status (`hb_check_connector_status`)
- Account balance (`hb_get_balance`)

**Location:** `agents/system_init.py`

### EntryExecutionAgent

Updated to use MCP for:
- Placing entry orders (`hb_place_order`)

**Location:** `agents/entry_execution.py`

### ExitExecutionAgent

Updated to use MCP for:
- Closing positions (`hb_close_position`)

**Location:** `agents/exit_execution.py`

## Development Mode

The system includes fallback mechanisms for development:

1. **Mock Mode**: When MCP server is not running, agents use mock responses
2. **Disabled Mode**: When MCP is disabled in config, agents use mock data
3. **Live Mode**: When MCP server is running and connected to Hummingbot

Each response includes an `mcp_mode` field indicating the current mode:

```python
{
    'success': True,
    'order_id': 'ORDER-12345',
    'mcp_mode': 'mock'  # or 'live' or 'disabled'
}
```

## Testing

Run MCP integration tests:

```bash
# Run all MCP tests
pytest tests/test_mcp_integration.py -v

# Run specific test class
pytest tests/test_mcp_integration.py::TestHummingbotMCPClient -v

# Run with coverage
pytest tests/test_mcp_integration.py --cov=tools.mcp_client --cov-report=html
```

## Installation

1. Install MCP dependency:
```bash
pip install mcp>=1.0.0
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

2. Verify installation:
```bash
python -c "import mcp; print('MCP installed successfully')"
```

## Usage Examples

### Example 1: Check System Health

```python
from agents.system_init import SystemInitAgent

# Initialize agent
agent = SystemInitAgent('system_init', config)

# Execute initialization
state = await agent.execute(trading_state)

# Check results
init_results = state['agent_outputs']['system_init']['result']
print(f"Gateway Status: {init_results['checks']['hummingbot']['status']}")
print(f"Broker Status: {init_results['checks']['broker']['status']}")
print(f"Balance: ${init_results['checks']['balance']['balance']:,.2f}")
```

### Example 2: Place Entry Order

```python
from agents.entry_execution import EntryExecutionAgent

# Initialize agent
agent = EntryExecutionAgent('entry_execution', config)

# Execute entry logic
state = await agent.execute(trading_state)

# Check order result
entry_result = state['agent_outputs']['entry_execution']['result']
if entry_result['status'] == 'executed':
    order = entry_result['order']
    print(f"Order ID: {order['order_id']}")
    print(f"Execution Price: {order['execution_price']}")
```

### Example 3: Close Position

```python
from agents.exit_execution import ExitExecutionAgent

# Initialize agent
agent = ExitExecutionAgent('exit_execution', config)

# Execute exit logic
state = await agent.execute(trading_state)

# Check exit result
exit_result = state['agent_outputs']['exit_execution']['result']
for exit_info in exit_result.get('exits', []):
    print(f"Exit Type: {exit_info['exit_type']}")
    print(f"Order ID: {exit_info['order_id']}")
```

## Error Handling

The MCP integration includes comprehensive error handling:

```python
try:
    result = await agent.hb_place_order(
        connector="oanda",
        trading_pair="GBP/USD",
        side="buy",
        amount=1.0
    )
except RuntimeError as e:
    # MCP client not initialized
    logger.error("MCP error", error=str(e))
except Exception as e:
    # Other errors (API failures, network issues, etc.)
    logger.error("Order placement failed", error=str(e))
```

## Logging

MCP operations are logged with structured logging:

```python
# Logs include:
- mcp_tool_called: When a tool is invoked
- mcp_tool_execution_failed: When tool execution fails
- mcp_server_not_running: When fallback to mock is used
- mcp_not_available: When MCP is disabled
```

View logs:
```bash
# Filter MCP-related logs
tail -f logs/ytc.log | grep mcp
```

## Migration from Direct API Calls

**Before (Direct HTTP API):**
```python
import aiohttp

async with aiohttp.ClientSession() as session:
    async with session.post(
        f"{self.hummingbot_url}/create_order",
        json=order_params
    ) as resp:
        result = await resp.json()
```

**After (MCP):**
```python
result = await self.hb_place_order(
    connector="oanda",
    trading_pair="GBP/USD",
    side="buy",
    amount=1.0
)
```

## Benefits

1. **Type Safety**: Input schemas validate parameters
2. **Standardization**: Consistent interface across all trading operations
3. **Error Handling**: Structured error responses
4. **Logging**: Automatic logging of all tool calls
5. **Testing**: Easy to mock and test
6. **Scalability**: Add new tools without changing agent code
7. **Development**: Mock fallback for testing without live gateway

## Troubleshooting

### MCP Client Not Available

**Error:** `MCP client not initialized`

**Solution:** Check that:
1. MCP is installed: `pip install mcp`
2. MCP is enabled in config: `mcp_enabled: true`
3. Agent has `mcp_client` initialized

### Mock Data Being Used

**Warning:** `mcp_server_not_running`

**Solution:** This is normal in development. To use live data:
1. Start Hummingbot Gateway
2. Ensure gateway URL is correct in config
3. MCP will automatically switch to live mode

### Tool Not Found Error

**Error:** `Tool {name} was not used in response`

**Solution:**
1. Check tool name is correct
2. Verify tool is enabled in config
3. Check Claude API response for errors

## Future Enhancements

1. **Standalone MCP Server**: Run MCP server as separate process
2. **WebSocket Support**: Real-time market data streaming
3. **Advanced Tools**: Portfolio optimization, risk calculations
4. **Multi-Connector**: Support multiple exchanges simultaneously
5. **Caching**: Intelligent caching of market data and positions
6. **Rate Limiting**: Automatic rate limit handling

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Anthropic Claude Tools API](https://docs.anthropic.com/claude/docs/tool-use)
- [Hummingbot Gateway API](https://docs.hummingbot.org/gateway/)

## Support

For issues or questions:
1. Check logs: `logs/ytc.log`
2. Run tests: `pytest tests/test_mcp_integration.py -v`
3. Review configuration: `config/mcp_config.yaml`
4. Check MCP server status: Run server standalone and verify output

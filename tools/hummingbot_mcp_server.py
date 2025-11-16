"""
MCP Server for Hummingbot Gateway Integration
Exposes Hummingbot Gateway functionality as MCP tools for Claude agents
"""

import json
import asyncio
from typing import Any, Dict, List, Optional, Sequence
from contextlib import AsyncExitStack
import structlog
import aiohttp

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: MCP not installed. Run: pip install mcp")

logger = structlog.get_logger()


class HummingbotMCPServer:
    """
    MCP Server that wraps Hummingbot Gateway API.
    Provides tools for trading operations, market data, and account management.
    """

    def __init__(self, gateway_url: str = "http://localhost:15888"):
        """
        Initialize MCP server for Hummingbot.

        Args:
            gateway_url: URL of Hummingbot Gateway service
        """
        if not MCP_AVAILABLE:
            raise ImportError("MCP package not installed. Run: pip install mcp")

        self.gateway_url = gateway_url.rstrip('/')
        self.server = Server("hummingbot-gateway")
        self.session: Optional[aiohttp.ClientSession] = None

        logger.info("hummingbot_mcp_server_initialized", gateway_url=gateway_url)

        # Register all tools
        self._register_tools()

    def _register_tools(self):
        """Register all Hummingbot tools with MCP server"""

        # Tool 1: Place Order
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="place_order",
                    description="Place a trading order (market or limit) via Hummingbot Gateway",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connector": {
                                "type": "string",
                                "description": "Exchange connector name (e.g., 'oanda', 'binance')"
                            },
                            "trading_pair": {
                                "type": "string",
                                "description": "Trading pair symbol (e.g., 'GBP/USD', 'BTC-USDT')"
                            },
                            "side": {
                                "type": "string",
                                "enum": ["buy", "sell"],
                                "description": "Order side: buy or sell"
                            },
                            "amount": {
                                "type": "number",
                                "description": "Order amount in base currency or lots"
                            },
                            "order_type": {
                                "type": "string",
                                "enum": ["market", "limit"],
                                "description": "Order type: market or limit"
                            },
                            "price": {
                                "type": "number",
                                "description": "Limit price (required for limit orders, optional for market)"
                            },
                            "time_in_force": {
                                "type": "string",
                                "enum": ["GTC", "IOC", "FOK"],
                                "description": "Time in force (optional, default: GTC)"
                            }
                        },
                        "required": ["connector", "trading_pair", "side", "amount", "order_type"]
                    }
                ),

                Tool(
                    name="cancel_order",
                    description="Cancel an existing open order",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connector": {
                                "type": "string",
                                "description": "Exchange connector name"
                            },
                            "order_id": {
                                "type": "string",
                                "description": "Unique order identifier"
                            },
                            "trading_pair": {
                                "type": "string",
                                "description": "Trading pair (optional, helps with lookup)"
                            }
                        },
                        "required": ["connector", "order_id"]
                    }
                ),

                Tool(
                    name="get_balance",
                    description="Get account balance for a specific connector",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connector": {
                                "type": "string",
                                "description": "Exchange connector name (e.g., 'oanda')"
                            },
                            "currency": {
                                "type": "string",
                                "description": "Specific currency to query (optional, returns all if not specified)"
                            }
                        },
                        "required": ["connector"]
                    }
                ),

                Tool(
                    name="get_positions",
                    description="Get all open positions for a connector",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connector": {
                                "type": "string",
                                "description": "Exchange connector name"
                            },
                            "trading_pair": {
                                "type": "string",
                                "description": "Filter by specific trading pair (optional)"
                            }
                        },
                        "required": ["connector"]
                    }
                ),

                Tool(
                    name="get_market_data",
                    description="Get current market price and ticker data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connector": {
                                "type": "string",
                                "description": "Exchange connector name"
                            },
                            "trading_pair": {
                                "type": "string",
                                "description": "Trading pair symbol (e.g., 'GBP/USD')"
                            }
                        },
                        "required": ["connector", "trading_pair"]
                    }
                ),

                Tool(
                    name="get_order_status",
                    description="Get status of a specific order",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connector": {
                                "type": "string",
                                "description": "Exchange connector name"
                            },
                            "order_id": {
                                "type": "string",
                                "description": "Order ID to check"
                            }
                        },
                        "required": ["connector", "order_id"]
                    }
                ),

                Tool(
                    name="check_gateway_status",
                    description="Check if Hummingbot Gateway is running and healthy",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),

                Tool(
                    name="check_connector_status",
                    description="Check if a specific connector is available and configured",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connector": {
                                "type": "string",
                                "description": "Connector name to check (e.g., 'oanda')"
                            }
                        },
                        "required": ["connector"]
                    }
                ),

                Tool(
                    name="get_open_orders",
                    description="Get all open orders for a connector",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connector": {
                                "type": "string",
                                "description": "Exchange connector name"
                            },
                            "trading_pair": {
                                "type": "string",
                                "description": "Filter by trading pair (optional)"
                            }
                        },
                        "required": ["connector"]
                    }
                ),

                Tool(
                    name="close_position",
                    description="Close an existing open position",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connector": {
                                "type": "string",
                                "description": "Exchange connector name"
                            },
                            "trading_pair": {
                                "type": "string",
                                "description": "Trading pair of position to close"
                            },
                            "amount": {
                                "type": "number",
                                "description": "Amount to close (optional, closes entire position if not specified)"
                            }
                        },
                        "required": ["connector", "trading_pair"]
                    }
                )
            ]

        # Tool execution handler
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
            """Execute tool by calling Hummingbot Gateway API"""
            logger.info("mcp_tool_called", tool=name, arguments=arguments)

            try:
                result = await self._execute_tool(name, arguments)
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except Exception as e:
                logger.error("mcp_tool_execution_failed", tool=name, error=str(e))
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "tool": name,
                        "arguments": arguments
                    }, indent=2)
                )]

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by calling the appropriate Hummingbot Gateway endpoint.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            API response as dictionary
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            if name == "place_order":
                return await self._place_order(arguments)
            elif name == "cancel_order":
                return await self._cancel_order(arguments)
            elif name == "get_balance":
                return await self._get_balance(arguments)
            elif name == "get_positions":
                return await self._get_positions(arguments)
            elif name == "get_market_data":
                return await self._get_market_data(arguments)
            elif name == "get_order_status":
                return await self._get_order_status(arguments)
            elif name == "check_gateway_status":
                return await self._check_gateway_status()
            elif name == "check_connector_status":
                return await self._check_connector_status(arguments)
            elif name == "get_open_orders":
                return await self._get_open_orders(arguments)
            elif name == "close_position":
                return await self._close_position(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

        except aiohttp.ClientError as e:
            logger.error("hummingbot_api_error", error=str(e), tool=name)
            raise Exception(f"Hummingbot Gateway API error: {str(e)}")

    async def _place_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Place a trading order"""
        endpoint = f"{self.gateway_url}/api/v1/order"

        payload = {
            "connector": params["connector"],
            "tradingPair": params["trading_pair"],
            "side": params["side"],
            "amount": params["amount"],
            "orderType": params["order_type"]
        }

        if "price" in params:
            payload["price"] = params["price"]
        if "time_in_force" in params:
            payload["timeInForce"] = params["time_in_force"]

        async with self.session.post(endpoint, json=payload) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                error_text = await resp.text()
                raise Exception(f"Order placement failed: {error_text}")

    async def _cancel_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel an order"""
        endpoint = f"{self.gateway_url}/api/v1/order/cancel"

        payload = {
            "connector": params["connector"],
            "orderId": params["order_id"]
        }

        if "trading_pair" in params:
            payload["tradingPair"] = params["trading_pair"]

        async with self.session.post(endpoint, json=payload) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                error_text = await resp.text()
                raise Exception(f"Order cancellation failed: {error_text}")

    async def _get_balance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get account balance"""
        endpoint = f"{self.gateway_url}/api/v1/balance"

        query_params = {"connector": params["connector"]}
        if "currency" in params:
            query_params["currency"] = params["currency"]

        async with self.session.get(endpoint, params=query_params) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                error_text = await resp.text()
                raise Exception(f"Balance retrieval failed: {error_text}")

    async def _get_positions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get open positions"""
        endpoint = f"{self.gateway_url}/api/v1/positions"

        query_params = {"connector": params["connector"]}
        if "trading_pair" in params:
            query_params["tradingPair"] = params["trading_pair"]

        async with self.session.get(endpoint, params=query_params) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                error_text = await resp.text()
                raise Exception(f"Positions retrieval failed: {error_text}")

    async def _get_market_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get market price data"""
        endpoint = f"{self.gateway_url}/api/v1/ticker"

        query_params = {
            "connector": params["connector"],
            "tradingPair": params["trading_pair"]
        }

        async with self.session.get(endpoint, params=query_params) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                error_text = await resp.text()
                raise Exception(f"Market data retrieval failed: {error_text}")

    async def _get_order_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get order status"""
        endpoint = f"{self.gateway_url}/api/v1/order"

        query_params = {
            "connector": params["connector"],
            "orderId": params["order_id"]
        }

        async with self.session.get(endpoint, params=query_params) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                error_text = await resp.text()
                raise Exception(f"Order status retrieval failed: {error_text}")

    async def _check_gateway_status(self) -> Dict[str, Any]:
        """Check gateway health"""
        endpoint = f"{self.gateway_url}/api/v1/status"

        try:
            async with self.session.get(endpoint, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "status": "healthy",
                        "gateway_url": self.gateway_url,
                        "response": data
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "gateway_url": self.gateway_url,
                        "http_status": resp.status
                    }
        except Exception as e:
            return {
                "status": "unreachable",
                "gateway_url": self.gateway_url,
                "error": str(e)
            }

    async def _check_connector_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check connector availability"""
        endpoint = f"{self.gateway_url}/api/v1/connectors"

        async with self.session.get(endpoint) as resp:
            if resp.status == 200:
                data = await resp.json()
                connectors = data.get("connectors", [])

                connector_name = params["connector"]
                is_available = connector_name in connectors

                return {
                    "connector": connector_name,
                    "available": is_available,
                    "all_connectors": connectors
                }
            else:
                error_text = await resp.text()
                raise Exception(f"Connector status check failed: {error_text}")

    async def _get_open_orders(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all open orders"""
        endpoint = f"{self.gateway_url}/api/v1/orders"

        query_params = {"connector": params["connector"]}
        if "trading_pair" in params:
            query_params["tradingPair"] = params["trading_pair"]

        async with self.session.get(endpoint, params=query_params) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                error_text = await resp.text()
                raise Exception(f"Open orders retrieval failed: {error_text}")

    async def _close_position(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Close a position by placing opposite order"""
        # First, get the current position
        positions = await self._get_positions({
            "connector": params["connector"],
            "trading_pair": params["trading_pair"]
        })

        if not positions.get("positions"):
            return {
                "status": "no_position",
                "message": f"No open position for {params['trading_pair']}"
            }

        position = positions["positions"][0]
        position_size = position.get("amount", 0)

        if position_size == 0:
            return {
                "status": "no_position",
                "message": f"Position size is 0 for {params['trading_pair']}"
            }

        # Determine close amount
        close_amount = params.get("amount", position_size)

        # Determine opposite side
        is_long = position.get("side", "").lower() == "long" or position_size > 0
        close_side = "sell" if is_long else "buy"

        # Place market order to close
        return await self._place_order({
            "connector": params["connector"],
            "trading_pair": params["trading_pair"],
            "side": close_side,
            "amount": abs(close_amount),
            "order_type": "market"
        })

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
            self.session = None

    async def run(self):
        """Run the MCP server"""
        logger.info("starting_hummingbot_mcp_server", gateway_url=self.gateway_url)

        async with AsyncExitStack() as stack:
            # Initialize session
            self.session = await stack.enter_async_context(aiohttp.ClientSession())

            # Run MCP server
            await stdio_server(self.server)


async def main():
    """Main entry point for running MCP server standalone"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    gateway_url = os.getenv("HUMMINGBOT_GATEWAY_URL", "http://localhost:15888")
    server = HummingbotMCPServer(gateway_url)

    try:
        await server.run()
    finally:
        await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

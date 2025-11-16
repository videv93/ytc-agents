"""
MCP Client for YTC Agents
Provides a simple interface for agents to use MCP tools
"""

import json
from typing import Any, Dict, List, Optional
import structlog
from anthropic import Anthropic

logger = structlog.get_logger()


class HummingbotMCPClient:
    """
    Client for interacting with Hummingbot via MCP tools.
    Wraps the Claude API tool calling mechanism with a simple interface.
    """

    def __init__(self, anthropic_client: Anthropic, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize MCP client.

        Args:
            anthropic_client: Anthropic client instance
            model: Claude model to use for tool calling
        """
        self.client = anthropic_client
        self.model = model
        self.logger = logger.bind(component="mcp_client")

        # Define Hummingbot MCP tools
        self.tools = self._get_tools_definition()

    def _get_tools_definition(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for Claude.
        These match the tools provided by the MCP server.
        """
        return [
            {
                "name": "place_order",
                "description": "Place a trading order (market or limit) via Hummingbot Gateway",
                "input_schema": {
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
            },
            {
                "name": "cancel_order",
                "description": "Cancel an existing open order",
                "input_schema": {
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
            },
            {
                "name": "get_balance",
                "description": "Get account balance for a specific connector",
                "input_schema": {
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
            },
            {
                "name": "get_positions",
                "description": "Get all open positions for a connector",
                "input_schema": {
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
            },
            {
                "name": "get_market_data",
                "description": "Get current market price and ticker data",
                "input_schema": {
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
            },
            {
                "name": "get_order_status",
                "description": "Get status of a specific order",
                "input_schema": {
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
            },
            {
                "name": "check_gateway_status",
                "description": "Check if Hummingbot Gateway is running and healthy",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "check_connector_status",
                "description": "Check if a specific connector is available and configured",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "connector": {
                            "type": "string",
                            "description": "Connector name to check (e.g., 'oanda')"
                        }
                    },
                    "required": ["connector"]
                }
            },
            {
                "name": "get_open_orders",
                "description": "Get all open orders for a connector",
                "input_schema": {
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
            },
            {
                "name": "close_position",
                "description": "Close an existing open position",
                "input_schema": {
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
            }
        ]

    async def call_tool(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call a Hummingbot MCP tool directly.

        Args:
            tool_name: Name of the tool to call
            tool_params: Parameters for the tool
            context: Optional context to provide to Claude

        Returns:
            Tool execution result as dictionary

        Raises:
            ValueError: If tool is not found or execution fails
        """
        self.logger.info("calling_mcp_tool", tool=tool_name, params=tool_params)

        # Build prompt for Claude
        prompt = f"""
Execute the {tool_name} tool with the following parameters:

{json.dumps(tool_params, indent=2)}
"""

        if context:
            prompt = f"{context}\n\n{prompt}"

        # Call Claude with tools
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            tools=self.tools
        )

        # Process response
        if response.stop_reason == "tool_use":
            # Extract tool use and result
            for content in response.content:
                if content.type == "tool_use" and content.name == tool_name:
                    # In a real MCP setup, this would call the MCP server
                    # For now, we'll return the input that would be sent
                    self.logger.info("tool_called", tool=content.name, input=content.input)

                    # Since we don't have the actual MCP server running,
                    # we return a structure indicating what would be called
                    return {
                        "tool": content.name,
                        "input": content.input,
                        "id": content.id,
                        "status": "would_execute",
                        "note": "MCP server integration required for actual execution"
                    }

            raise ValueError(f"Tool {tool_name} was not used in response")

        elif response.stop_reason == "end_turn":
            # Claude didn't use the tool
            text_content = [c.text for c in response.content if hasattr(c, 'text')]
            raise ValueError(f"Claude did not use the tool. Response: {text_content}")

        else:
            raise ValueError(f"Unexpected stop reason: {response.stop_reason}")

    async def place_order(
        self,
        connector: str,
        trading_pair: str,
        side: str,
        amount: float,
        order_type: str = "market",
        price: Optional[float] = None,
        time_in_force: str = "GTC"
    ) -> Dict[str, Any]:
        """
        Place a trading order.

        Args:
            connector: Exchange connector name
            trading_pair: Trading pair symbol
            side: Order side ('buy' or 'sell')
            amount: Order amount
            order_type: Order type ('market' or 'limit')
            price: Limit price (required for limit orders)
            time_in_force: Time in force

        Returns:
            Order result
        """
        params = {
            "connector": connector,
            "trading_pair": trading_pair,
            "side": side,
            "amount": amount,
            "order_type": order_type,
            "time_in_force": time_in_force
        }

        if price is not None:
            params["price"] = price

        return await self.call_tool("place_order", params)

    async def get_balance(self, connector: str, currency: Optional[str] = None) -> Dict[str, Any]:
        """
        Get account balance.

        Args:
            connector: Exchange connector name
            currency: Optional specific currency

        Returns:
            Balance information
        """
        params = {"connector": connector}
        if currency:
            params["currency"] = currency

        return await self.call_tool("get_balance", params)

    async def get_positions(
        self,
        connector: str,
        trading_pair: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get open positions.

        Args:
            connector: Exchange connector name
            trading_pair: Optional trading pair filter

        Returns:
            Positions information
        """
        params = {"connector": connector}
        if trading_pair:
            params["trading_pair"] = trading_pair

        return await self.call_tool("get_positions", params)

    async def close_position(
        self,
        connector: str,
        trading_pair: str,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Close an open position.

        Args:
            connector: Exchange connector name
            trading_pair: Trading pair of position
            amount: Amount to close (None = close all)

        Returns:
            Close result
        """
        params = {
            "connector": connector,
            "trading_pair": trading_pair
        }

        if amount is not None:
            params["amount"] = amount

        return await self.call_tool("close_position", params)

    async def check_gateway_status(self) -> Dict[str, Any]:
        """
        Check if Hummingbot Gateway is healthy.

        Returns:
            Gateway status
        """
        return await self.call_tool("check_gateway_status", {})

    async def check_connector_status(self, connector: str) -> Dict[str, Any]:
        """
        Check if a connector is available.

        Args:
            connector: Connector name to check

        Returns:
            Connector status
        """
        return await self.call_tool("check_connector_status", {"connector": connector})

    async def get_market_data(self, connector: str, trading_pair: str) -> Dict[str, Any]:
        """
        Get current market data.

        Args:
            connector: Exchange connector name
            trading_pair: Trading pair symbol

        Returns:
            Market data
        """
        return await self.call_tool(
            "get_market_data",
            {"connector": connector, "trading_pair": trading_pair}
        )

    async def cancel_order(
        self,
        connector: str,
        order_id: str,
        trading_pair: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel an order.

        Args:
            connector: Exchange connector name
            order_id: Order ID to cancel
            trading_pair: Optional trading pair

        Returns:
            Cancellation result
        """
        params = {
            "connector": connector,
            "order_id": order_id
        }

        if trading_pair:
            params["trading_pair"] = trading_pair

        return await self.call_tool("cancel_order", params)

    async def get_open_orders(
        self,
        connector: str,
        trading_pair: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all open orders.

        Args:
            connector: Exchange connector name
            trading_pair: Optional trading pair filter

        Returns:
            Open orders
        """
        params = {"connector": connector}
        if trading_pair:
            params["trading_pair"] = trading_pair

        return await self.call_tool("get_open_orders", params)

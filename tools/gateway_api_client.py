"""
Hummingbot Gateway API Client
Direct HTTP client for Hummingbot Gateway API integration
Uses the actual Hummingbot REST API endpoints (not MCP protocol)
"""

import aiohttp
from typing import Any, Dict, Optional
import structlog

logger = structlog.get_logger()


class HummingbotGatewayClient:
    """
    Direct HTTP client for Hummingbot Gateway API.
    Communicates directly with the Gateway REST API.
    """

    def __init__(
        self,
        gateway_url: str = "http://localhost:8000",
        account_name: str = "default",
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize Gateway API client.

        Args:
            gateway_url: Base URL of Hummingbot Gateway (default: http://localhost:8000)
            account_name: Default account name to use for trading
            username: Optional username for authentication
            password: Optional password for authentication
        """
        self.gateway_url = gateway_url.rstrip('/')
        self.account_name = account_name
        self.username = username
        self.password = password
        self.logger = logger.bind(component="gateway_client")
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth: Optional[aiohttp.BasicAuth] = None

        if username and password:
            self.auth = aiohttp.BasicAuth(username, password)

        self.logger.info("gateway_client_initialized", gateway_url=self.gateway_url, account=account_name, auth_enabled=bool(self.auth))

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Gateway API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data (for POST)
            params: Query parameters (for GET)

        Returns:
            Response data as dictionary
        """
        session = await self._get_session()
        url = f"{self.gateway_url}{endpoint}"

        self.logger.info("gateway_api_request", method=method, endpoint=endpoint, url=url)

        try:
            if method == "GET":
                async with session.get(url, params=params, auth=self.auth, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status in [200, 201]:
                        return await resp.json()
                    else:
                        error_text = await resp.text()
                        raise Exception(f"Gateway API error ({resp.status}): {error_text}")

            elif method == "POST":
                async with session.post(url, json=data, auth=self.auth, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status in [200, 201]:
                        return await resp.json()
                    else:
                        error_text = await resp.text()
                        raise Exception(f"Gateway API error ({resp.status}): {error_text}")

            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        except aiohttp.ClientError as e:
            self.logger.error("gateway_request_failed", error=str(e), endpoint=endpoint)
            raise Exception(f"Gateway API request failed: {str(e)}")

    # ==================== Health Check ====================

    async def check_gateway_status(self) -> Dict[str, Any]:
        """
        Check if Hummingbot Gateway is running and healthy.

        Returns:
            Gateway status
        """
        try:
            # Check if we can get portfolio state (indicates gateway is working)
            result = await self._request("POST", "/portfolio/state", data={})
            return {
                "status": "healthy",
                "gateway_url": self.gateway_url,
                "response": result
            }
        except Exception as e:
            self.logger.error("gateway_status_check_failed", error=str(e))
            return {
                "status": "unhealthy",
                "gateway_url": self.gateway_url,
                "error": str(e)
            }

    async def check_connector_status(self, connector: str) -> Dict[str, Any]:
        """
        Check if a specific connector is available.

        Args:
            connector: Connector name (e.g., 'oanda', 'binance')

        Returns:
            Connector status
        """
        try:
            # List available connectors
            result = await self._request("GET", "/connectors/")
            connectors = result.get("connectors", []) if isinstance(result, dict) else result
            is_available = connector in connectors

            return {
                "connector": connector,
                "available": is_available,
                "all_connectors": connectors
            }
        except Exception as e:
            self.logger.error("connector_status_check_failed", error=str(e), connector=connector)
            return {
                "connector": connector,
                "available": False,
                "error": str(e)
            }

    # ==================== Portfolio & Balance ====================

    async def get_balance(self, connector: str, account_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get account balance for a specific connector.

        Args:
            connector: Exchange connector name
            account_name: Optional account name (uses default if not provided)

        Returns:
            Balance information
        """
        account = account_name or self.account_name
        
        try:
            # Get portfolio state
            result = await self._request(
                "POST",
                "/portfolio/state",
                data={}
            )

            # Parse balance from portfolio state
            # Response structure: {account_name: {connector_name: [{token, units, available_units, ...}]}}
            if isinstance(result, dict):
                # Try to find the account in the response
                account_data = None
                if account in result:
                    account_data = result[account]
                elif "master_account" in result:
                    account_data = result["master_account"]
                
                if account_data:
                    connector_data = account_data.get(connector, [])
                    if connector_data:
                        # Sum available units (not units, which might include short positions)
                        total_balance = sum(float(item.get("available_units", 0)) for item in connector_data)
                        # Get primary currency (first token or USDT if available)
                        primary_currency = next(
                            (item.get("token", "USDT") for item in connector_data if item.get("token") == "USDT"),
                            connector_data[0].get("token", "USDT") if connector_data else "USDT"
                        )
                        return {
                            "status": "ok",
                            "account": account,
                            "connector": connector,
                            "balance": total_balance,
                            "currency": primary_currency,
                            "details": connector_data
                        }

            return {
                "status": "ok",
                "account": account,
                "connector": connector,
                "balance": 0.0,
                "currency": "USDT",
                "details": []
            }

        except Exception as e:
            self.logger.error("balance_fetch_failed", error=str(e), connector=connector, account=account)
            return {
                "status": "error",
                "error": str(e),
                "balance": 0.0
            }

    async def get_positions(
        self,
        connector: str,
        trading_pair: Optional[str] = None,
        account_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get open positions.

        Args:
            connector: Exchange connector name
            trading_pair: Optional trading pair filter
            account_name: Optional account name

        Returns:
            Positions information
        """
        account = account_name or self.account_name
        
        try:
            # Build filter request
            filter_data = {}
            if account and account != "all":
                filter_data["account_names"] = [account]
            if connector and connector != "all":
                filter_data["connector_names"] = [connector]
            if trading_pair:
                filter_data["trading_pairs"] = [trading_pair]

            result = await self._request("POST", "/trading/positions", data=filter_data)

            # Parse positions from response
            if isinstance(result, dict):
                positions = result.get("rows", []) if "rows" in result else result.get("positions", [])
                return {
                    "status": "ok",
                    "positions": positions,
                    "count": len(positions)
                }

            return {
                "status": "ok",
                "positions": result if isinstance(result, list) else [],
                "count": len(result) if isinstance(result, list) else 0
            }

        except Exception as e:
            self.logger.error("positions_fetch_failed", error=str(e), connector=connector)
            return {
                "status": "error",
                "error": str(e),
                "positions": [],
                "count": 0
            }

    # ==================== Trading ====================

    async def place_order(
        self,
        connector: str,
        trading_pair: str,
        side: str,
        amount: float,
        order_type: str = "MARKET",
        price: Optional[float] = None,
        account_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Place a trading order.

        Args:
            connector: Exchange connector name
            trading_pair: Trading pair symbol (e.g., 'BTC-USDT')
            side: Order side ('buy' or 'sell', converts to 'BUY' or 'SELL')
            amount: Order amount
            order_type: Order type ('market' or 'limit', converts to 'MARKET' or 'LIMIT')
            price: Limit price (required for limit orders)
            account_name: Optional account name

        Returns:
            Order result
        """
        account = account_name or self.account_name
        
        try:
            # Normalize inputs
            trade_type = "BUY" if side.lower() == "buy" else "SELL"
            order_enum = order_type.upper() if order_type.upper() in ["MARKET", "LIMIT", "LIMIT_MAKER"] else "MARKET"

            payload = {
                "account_name": account,
                "connector_name": connector,
                "trading_pair": trading_pair,
                "trade_type": trade_type,
                "amount": amount,
                "order_type": order_enum
            }

            if price is not None:
                payload["price"] = price

            self.logger.info("placing_order", account=account, connector=connector, pair=trading_pair, side=side, amount=amount)

            result = await self._request("POST", "/trading/orders", data=payload)

            return {
                "status": "executed",
                "order": result
            }

        except Exception as e:
            self.logger.error("order_placement_failed", error=str(e), connector=connector)
            return {
                "status": "error",
                "error": str(e)
            }

    async def cancel_order(
        self,
        connector: str,
        order_id: str,
        trading_pair: str,
        account_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel an order.

        Args:
            connector: Exchange connector name
            order_id: Order ID to cancel
            trading_pair: Trading pair of the order
            account_name: Optional account name

        Returns:
            Cancellation result
        """
        account = account_name or self.account_name
        
        try:
            endpoint = f"/trading/{account}/{connector}/orders/{order_id}/cancel"
            result = await self._request("POST", endpoint, data={"trading_pair": trading_pair})

            return {
                "status": "cancelled",
                "order_id": order_id,
                "result": result
            }

        except Exception as e:
            self.logger.error("order_cancellation_failed", error=str(e), order_id=order_id)
            return {
                "status": "error",
                "error": str(e)
            }

    async def get_open_orders(
        self,
        connector: str,
        trading_pair: Optional[str] = None,
        account_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all open orders.

        Args:
            connector: Exchange connector name
            trading_pair: Optional trading pair filter
            account_name: Optional account name

        Returns:
            Open orders
        """
        account = account_name or self.account_name
        
        try:
            filter_data = {}
            if account and account != "all":
                filter_data["account_names"] = [account]
            if connector and connector != "all":
                filter_data["connector_names"] = [connector]
            if trading_pair:
                filter_data["trading_pairs"] = [trading_pair]

            result = await self._request("POST", "/trading/orders/active", data=filter_data)

            if isinstance(result, dict):
                orders = result.get("rows", []) if "rows" in result else result.get("orders", [])
            else:
                orders = result if isinstance(result, list) else []

            return {
                "status": "ok",
                "orders": orders,
                "count": len(orders)
            }

        except Exception as e:
            self.logger.error("open_orders_fetch_failed", error=str(e), connector=connector)
            return {
                "status": "error",
                "error": str(e),
                "orders": [],
                "count": 0
            }

    async def close_position(
        self,
        connector: str,
        trading_pair: str,
        amount: Optional[float] = None,
        account_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Close an open position.

        Args:
            connector: Exchange connector name
            trading_pair: Trading pair of position
            amount: Amount to close (None = close all)
            account_name: Optional account name

        Returns:
            Close result
        """
        account = account_name or self.account_name
        
        try:
            # Get current position to determine side
            positions = await self.get_positions(connector, trading_pair, account)

            if not positions.get("positions"):
                return {
                    "status": "no_position",
                    "message": f"No open position for {trading_pair}"
                }

            position = positions["positions"][0]
            position_size = float(position.get("amount", 0))

            if position_size == 0:
                return {
                    "status": "no_position",
                    "message": f"Position size is 0 for {trading_pair}"
                }

            # Determine close amount and side
            close_amount = amount if amount is not None else abs(position_size)
            is_long = position_size > 0
            close_side = "sell" if is_long else "buy"

            # Place market order to close
            return await self.place_order(
                connector=connector,
                trading_pair=trading_pair,
                side=close_side,
                amount=close_amount,
                order_type="market",
                account_name=account
            )

        except Exception as e:
            self.logger.error("position_close_failed", error=str(e), trading_pair=trading_pair)
            return {
                "status": "error",
                "error": str(e)
            }

    # ==================== Market Data ====================

    async def get_market_data(self, connector: str, trading_pair: str) -> Dict[str, Any]:
        """
        Get current market data (price).

        Args:
            connector: Exchange connector name
            trading_pair: Trading pair symbol

        Returns:
            Market data
        """
        try:
            payload = {
                "connector_name": connector,
                "trading_pairs": [trading_pair]
            }

            result = await self._request("POST", "/market-data/prices", data=payload)

            # Parse prices from response
            if isinstance(result, dict) and "prices" in result:
                prices = result["prices"]
                if isinstance(prices, dict) and trading_pair in prices:
                    return {
                        "status": "ok",
                        "connector": connector,
                        "trading_pair": trading_pair,
                        "price": float(prices[trading_pair]),
                        "timestamp": result.get("timestamp")
                    }

            return {
                "status": "error",
                "error": "No price data returned",
                "connector": connector,
                "trading_pair": trading_pair
            }

        except Exception as e:
            self.logger.error("market_data_fetch_failed", error=str(e), trading_pair=trading_pair)
            return {
                "status": "error",
                "error": str(e),
                "connector": connector,
                "trading_pair": trading_pair
            }

    async def get_order_book(self, connector: str, trading_pair: str) -> Dict[str, Any]:
        """
        Get order book data.

        Args:
            connector: Exchange connector name
            trading_pair: Trading pair symbol

        Returns:
            Order book data
        """
        try:
            payload = {
                "connector_name": connector,
                "trading_pairs": [trading_pair]
            }

            result = await self._request("POST", "/market-data/order-book", data=payload)

            return {
                "status": "ok",
                "connector": connector,
                "trading_pair": trading_pair,
                "order_book": result
            }

        except Exception as e:
            self.logger.error("order_book_fetch_failed", error=str(e), trading_pair=trading_pair)
            return {
                "status": "error",
                "error": str(e),
                "connector": connector,
                "trading_pair": trading_pair
            }

    async def get_trades(
        self,
        connector: Optional[str] = None,
        trading_pair: Optional[str] = None,
        account_name: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get trade history.

        Args:
            connector: Optional connector filter
            trading_pair: Optional trading pair filter
            account_name: Optional account name filter
            limit: Number of trades to return

        Returns:
            Trade history
        """
        try:
            filter_data = {}
            if account_name:
                filter_data["account_names"] = [account_name]
            if connector:
                filter_data["connector_names"] = [connector]
            if trading_pair:
                filter_data["trading_pairs"] = [trading_pair]
            if limit:
                filter_data["limit"] = limit

            result = await self._request("POST", "/trading/trades", data=filter_data)

            if isinstance(result, dict):
                trades = result.get("rows", []) if "rows" in result else result.get("trades", [])
            else:
                trades = result if isinstance(result, list) else []

            return {
                "status": "ok",
                "trades": trades,
                "count": len(trades)
            }

        except Exception as e:
            self.logger.error("trades_fetch_failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "trades": [],
                "count": 0
            }

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("gateway_client_closed")

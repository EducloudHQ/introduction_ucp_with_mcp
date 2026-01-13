from typing import Any
import argparse
import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession
from pydantic import BaseModel, Field

from ucp_sdk.models.schemas.shopping.types.postal_address import PostalAddress
from ucp_sdk.models.schemas.ucp import ResponseCheckout as UcpMetadata
from .models.product_types import ProductResults, Product

from .store import RetailStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

store = RetailStore()

# Initialize FastMCP server
mcp = FastMCP(
    name="UCP Shopping Service",
    instructions="""
    This MCP server provides access to UCP (Universal Commerce Protocol) shopping
    capabilities. You can:

    1. Browse Products: Use search_shopping_catalog to explore the catalog
    2. Create Checkout: add_to_checkout automatically creates a checkout if none exists
    3. Add Items: Use add_to_checkout to add products to your cart
    4. Update Address: Use update_customer_details to configure delivery
    5. Complete Purchase: Use complete_checkout to finalize the order
    6. Track Orders: Use ucp://orders/{order_id} resource to check order status

    Start by searching for products, then guide the user through checkout.
    """,
)

# Helper to get default metadata (mock)
def _get_default_metadata() -> UcpMetadata:
    return UcpMetadata.model_validate(store._ucp_metadata["ucp"])

@mcp.tool()
async def search_shopping_catalog(query: str = "") -> ProductResults:
    """Searches for products in the catalog based on a query string.

    Args:
        query: Searching keywords or categories. Returns all products if query is empty.
    """
    if not query:
        return store.get_all_products()
    return store.search_products(query)

@mcp.tool()
async def add_to_checkout(
    product_id: str, quantity: int = 1, checkout_id: str = None
) -> Any:
    """Adds a product to the checkout. Creates a new checkout if checkout_id is not provided.

    Args:
        product_id: ID of the product to add.
        quantity: Quantity of the product.
        checkout_id: Optional ID of an existing checkout.
    """
    metadata = _get_default_metadata()
    return store.add_to_checkout(metadata, product_id, quantity, checkout_id)

@mcp.tool()
async def remove_from_checkout(checkout_id: str, product_id: str) -> Any:
    """Removes a product from the checkout.

    Args:
        checkout_id: ID of the checkout.
        product_id: ID of the product to remove.
    """
    return store.remove_from_checkout(checkout_id, product_id)

@mcp.tool()
async def update_checkout(checkout_id: str, product_id: str, quantity: int) -> Any:
    """Updates the quantity of a product in the checkout.

    Args:
        checkout_id: ID of the checkout.
        product_id: ID of the product.
        quantity: New quantity.
    """
    return store.update_checkout(checkout_id, product_id, quantity)

@mcp.tool()
async def get_checkout(checkout_id: str) -> Any:
    """Retrieves the current state of a checkout.

    Args:
        checkout_id: ID of the checkout to retrieve.
    """
    return store.get_checkout(checkout_id)

@mcp.tool()
async def start_payment(checkout_id: str) -> Any:
    """Initiates the payment process for a checkout.

    Args:
        checkout_id: ID of the checkout to start payment for.
    """
    return store.start_payment(checkout_id)

@mcp.tool()
async def update_customer_details(
    checkout_id: str, address: dict, email: str = None
) -> Any:
    """Updates the customer (shipping) details for a checkout.

    Args:
        checkout_id: ID of the checkout.
        address: Dictionary containing address fields (name, address_line1, city, region, postal_code, country).
        email: Optional buyer email address.
    """
    if email:
        first_name = None
        last_name = None
        full_name = address.get("name")
        if full_name:
            parts = full_name.split(maxsplit=1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""
            
        store.set_buyer(
            checkout_id, 
            email=email, 
            first_name=first_name, 
            last_name=last_name
        )
    postal_address = PostalAddress.model_validate(address)
    return store.add_delivery_address(checkout_id, postal_address)

@mcp.tool()
async def complete_checkout(checkout_id: str) -> Any:
    """Finalizes the checkout and places the order.

    Args:
        checkout_id: ID of the checkout to complete.
    """
    return store.place_order(checkout_id)

@mcp.resource("ucp://catalog/products")
async def list_products() -> ProductResults:
    """Returns the full product catalog."""
    return store.get_all_products()

@mcp.resource("ucp://checkout/{checkout_id}")
async def get_checkout_resource(checkout_id: str) -> Any:
    """Returns the current state of a specific checkout."""
    return store.get_checkout(checkout_id)

@mcp.resource("ucp://discovery/profile")
async def get_ucp_profile() -> dict:
    """Returns the merchant's UCP capability profile."""
    return store._ucp_metadata

@mcp.resource("ucp://orders/{order_id}")
async def get_order_resource(order_id: str) -> Any:
    """Returns order confirmation details."""
    return store._orders.get(order_id)

@mcp.prompt()
def shopping_assistance() -> str:
    """A prompt to help users find and buy products."""
    return (
        "You are a helpful shopping assistant. Use the UCP Shopping Service to help "
        "the user find products in the catalog and guide them through the checkout process. "
        "Start by asking what they are looking for or show them the available products."
    )

def main():
    """Entry point for the UCP MCP Server."""
    parser = argparse.ArgumentParser(
        description="UCP MCP Server - Model Context Protocol for Universal Commerce"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="Transport mechanism (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP/SSE transport (default: 8000)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for HTTP/SSE transport (default: 0.0.0.0)",
    )

    args = parser.parse_args()

    logger.info(f"Starting UCP MCP Server with {args.transport} transport")

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "http":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    elif args.transport == "sse":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="sse")


if __name__ == "__main__":
    main()


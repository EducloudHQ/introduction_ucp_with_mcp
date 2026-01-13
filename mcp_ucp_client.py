#   Copyright 2026 UCP Authors
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
UCP MCP Client - Example client demonstrating MCP interaction with UCP server.

This module demonstrates how to connect to the UCP MCP server and perform
shopping operations using the MCP protocol. It showcases a complete "happy path"
user journey:

1. Connect to the MCP server
2. List available tools, resources, and prompts
3. Browse products
4. Create a checkout session and add items
5. Set shipping address and buyer details
6. Finalize order
7. Retrieve order confirmation via resource

Usage:
    # Connect to a running MCP server via stdio:
    PYTHONPATH=. uv run python mcp_ucp_client.py

    # Connect via HTTP:
    PYTHONPATH=. uv run python mcp_ucp_client.py --transport http --url http://localhost:8000/mcp
"""

import argparse
import asyncio
import json
import logging
import os
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import TextContent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def print_separator(title: str):
    """Print a visual separator with title."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


async def display_tools(session: ClientSession):
    """Display available tools from the server."""
    await print_separator("Available Tools")

    tools = await session.list_tools()
    for tool in tools.tools:
        print(f"  📦 {tool.name}")
        if tool.description:
            # Show first line of description
            desc = tool.description.split('\n')[0].strip()
            print(f"     {desc}")


async def display_resources(session: ClientSession):
    """Display available resources from the server."""
    await print_separator("Available Resources")

    # List static resources
    resources = await session.list_resources()
    for resource in resources.resources:
        print(f"  📄 {resource.uri}")
        if resource.name:
            print(f"     Name: {resource.name}")

    # List resource templates
    templates = await session.list_resource_templates()
    for template in templates.resourceTemplates:
        print(f"  📋 {template.uriTemplate} (template)")
        if template.name:
            print(f"     Name: {template.name}")


async def display_prompts(session: ClientSession):
    """Display available prompts from the server."""
    await print_separator("Available Prompts")

    prompts = await session.list_prompts()
    for prompt in prompts.prompts:
        print(f"  💬 {prompt.name}")
        if prompt.description:
            print(f"     {prompt.description}")


async def call_tool(session: ClientSession, name: str, arguments: dict[str, Any]) -> dict:
    """Call a tool and return the result as a dictionary."""
    logger.info(f"Calling tool: {name} with args: {arguments}")

    result = await session.call_tool(name, arguments=arguments)

    # Extract text content from result
    if result.content and len(result.content) > 0:
        content = result.content[0]
        if hasattr(content, 'text'):
            try:
                return json.loads(content.text)
            except json.JSONDecodeError:
                return {"text": content.text}

    return {"raw": str(result)}


async def read_resource(session: ClientSession, uri: str) -> str:
    from pydantic import AnyUrl
    logger.info(f"Attempting to read resource: {uri}")
    
    result = await session.read_resource(AnyUrl(uri))
    
    # Debug: Check if result or contents are empty
    if not result.contents:
        logger.error(f"Resource at {uri} returned no contents!")
        return ""
        
    content = result.contents[0]
    return content.text if hasattr(content, 'text') else str(content)


async def run_happy_path(session: ClientSession):
    """Run a complete shopping flow demonstrating UCP MCP capabilities."""

    await print_separator("🛒 UCP MCP Client - Happy Path Demo")
    print("This demo walks through a complete shopping experience using MCP.\n")

    # Step 1: Initialize connection
    print("✅ Connected to UCP MCP Server")
    await session.initialize()

    # Step 2: Display server capabilities
    await display_tools(session)
    await display_resources(session)
    await display_prompts(session)

    # Step 3: Browse products
    await print_separator("Step 1: Browse Products")
    results = await call_tool(session, "search_shopping_catalog", {"query": ""})

    if "results" in results:
        print(f"Found {len(results['results'])} products:\n")
        for p in results["results"]:
            print(f"  🌸 {p.get('name', 'Unknown Product')}")
            print(f"     ID: {p.get('productID', 'N/A')}")
            
            # Robustly get price
            price_val = 0.0
            offers = p.get('offers', [])
            if isinstance(offers, list) and offers:
                price_val = offers[0].get('price', 0.0)
            elif isinstance(offers, dict):
                price_val = offers.get('price', 0.0)
                
            try:
                price_val = float(price_val)
            except (ValueError, TypeError):
                price_val = 0.0
                
            print(f"     Price: ${price_val:.2f}")
            
            brand = p.get('brand', {})
            if isinstance(brand, dict):
                print(f"     Brand: {brand.get('name', 'N/A')}")
            
            print(f"     Description: {p.get('description', 'N/A')}")
            print(f"     Category: {p.get('category', 'N/A')}")
            
            images = p.get('image', [])
            if isinstance(images, list) and images:
                first_image = images[0]
                if isinstance(first_image, dict):
                    print(f"     Image: {first_image.get('url')}")
                else:
                    print(f"     Image: {first_image}")
            elif isinstance(images, str):
                print(f"     Image: {images}")
            print()

        # Pick the first product for the rest of the demo
        target_product = results["results"][0]
        product_id = target_product["productID"]
    else:
        print("❌ No products found.")
        return

    # Step 4: Create checkout session and add items
    await print_separator("Step 2: Add Items to Checkout")
    # add_to_checkout creates a checkout if checkout_id is not provided
    checkout = await call_tool(session, "add_to_checkout", {
        "product_id": product_id,
        "quantity": 2
    })

    if "id" in checkout:
        checkout_id = checkout["id"]
        print(f"✅ Created checkout session: {checkout_id}")
        print(f"   Status: {checkout['status']}")
        print(f"   Items added: {len(checkout['line_items'])}")

        # Step 5: Set shipping address and buyer details
        await print_separator("Step 3: Set Customer Details")
        result = await call_tool(session, "update_customer_details", {
            "checkout_id": checkout_id,
            "address": {
                "name": "Jane Doe",
                "address_line1": "123 Main Street",
                "city": "San Francisco",
                "region": "CA",
                "postal_code": "94102",
                "country": "US"
            },
            "email": "jane.doe@example.com"
        })
        print("✅ Customer details and shipping address set.")

        # Step 6: Review checkout via Resource
        await print_separator("Step 4: Review Checkout (via Resource)")
        checkout_resource = await read_resource(session, f"ucp://checkout/{checkout_id}")
        checkout_state = json.loads(checkout_resource)

        print("Current Checkout State:")
        print(f"  ID: {checkout_state['id']}")
        print(f"  Status: {checkout_state['status']}")
        print(f"\n  Items:")
        for item in checkout_state.get("line_items", []):
            item_data = item.get("item", {})
            name = item_data.get("title") or item_data.get("name") or "Unknown Product"
            price = item.get("price", 0)
            if price == 0 and item_data.get("price"):
                price = item_data.get("price")
            
            # Unit price is in minor units (cents)
            price_str = f"${price/100:.2f}"

            print(f"    - {item['quantity']}x {name}: {price_str}")
        
        # Totals
        for total in checkout_state.get("totals", []):
            print(f"  {total['type'].capitalize()}: ${total['amount']/100:.2f}")

        # Step 7: Finalize order
        await print_separator("Step 5: Finalize Order")
        print("Starting payment process...")
        await call_tool(session, "start_payment", {"checkout_id": checkout_id})
        
        print("Completing checkout...")
        order_response = await call_tool(session, "complete_checkout", {"checkout_id": checkout_id})

        if order_response.get("status") == "completed" and "order" in order_response:
            order = order_response["order"]
            print("\n🎉 Order Placed Successfully!")
            print(f"   Order ID: {order['id']}")
            print(f"   Status: {order_response['status']}")
            
            # Step 8: Verify order via resource
            await print_separator("Step 6: Check Order Status (via Resource)")
            order_data_str = await read_resource(session, f"ucp://orders/{order['id']}")
            order_details = json.loads(order_data_str)

            print(f"Order Confirmation for {order_details['order']['id']}:")
            
            # Robustly print seller and buyer if available
            order_info = order_details.get("order", {})
            seller = order_info.get("seller", {})
            if seller:
                print(f"  Seller: {seller.get('name', 'N/A')}")
            
            buyer = order_info.get("buyer", {})
            if buyer:
                full_name = buyer.get("full_name") or f"{buyer.get('first_name', '')} {buyer.get('last_name', '')}".strip()
                if full_name:
                    print(f"  Buyer: {full_name}")
                if buyer.get("email"):
                    print(f"  Email: {buyer.get('email')}")
        else:
            print(f"❌ Payment failed or incomplete: {order_response.get('status')}")
    else:
        print(f"❌ Failed to create checkout.")

    # Step 9: Read discovery profile resource
    await print_separator("Bonus: Read Discovery Profile")
    profile = await read_resource(session, "ucp://discovery/profile")
    print("UCP Discovery Profile (truncated):")
    profile_data = json.loads(profile)
    print(f"  Version: {profile_data.get('ucp', {}).get('version')}")
    print(f"  Capabilities: {[c['name'] for c in profile_data.get('ucp', {}).get('capabilities', [])]}")

    await print_separator("🎉 Demo Complete!")


async def run_stdio_client():
    """Connect to the server using stdio transport."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "src.mcp_ucp_server"],
        env=os.environ.copy()
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await run_happy_path(session)


async def run_http_client(url: str):
    """Connect to the server using HTTP transport."""
    from mcp.client.sse import sse_client

    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await run_happy_path(session)


def main():
    """Entry point for the UCP MCP Client."""
    parser = argparse.ArgumentParser(
        description="UCP MCP Client - Demonstrate shopping via MCP"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport mechanism (default: stdio)",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000/mcp",
        help="Server URL for HTTP transport (default: http://localhost:8000/mcp)",
    )

    args = parser.parse_args()

    if args.transport == "stdio":
        asyncio.run(run_stdio_client())
    else:
        asyncio.run(run_http_client(args.url))


if __name__ == "__main__":
    main()

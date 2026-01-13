import pytest
import asyncio
import json
from src.mcp_ucp_server import mcp
from src.models.product_types import ProductResults, Product

@pytest.mark.asyncio
async def test_search_shopping_catalog():
    # Test with empty query (should return all products)
    results = await mcp._tool_manager.call_tool("search_shopping_catalog", {"query": ""})
    assert isinstance(results, ProductResults)
    assert len(results.results) > 0

    # Test with a specific query
    results = await mcp._tool_manager.call_tool("search_shopping_catalog", {"query": "Cookies"})
    assert isinstance(results, ProductResults)
    assert any("Cookies" in p.name for p in results.results)

@pytest.mark.asyncio
async def test_full_shopping_flow():
    # 1. Search for a product
    print("\n[Step 1] Searching for 'Cookies'...")
    results = await mcp._tool_manager.call_tool("search_shopping_catalog", {"query": "Cookies"})
    product_id = results.results[0].product_id
    print(f"  Found product: {results.results[0].name} ({product_id})")

    # 2. Add to checkout (creates a new checkout)
    print("[Step 2] Adding to checkout...")
    checkout = await mcp._tool_manager.call_tool("add_to_checkout", {"product_id": product_id, "quantity": 2})
    checkout_id = checkout.id
    print(f"  Created checkout: {checkout_id}")
    assert checkout.id is not None
    assert len(checkout.line_items) == 1
    assert checkout.line_items[0].quantity == 2

    # 3. Update customer details
    print("[Step 3] Updating customer details...")
    address = {
        "name": "John Doe",
        "address_line1": "123 Main St",
        "city": "San Francisco",
        "region": "CA",
        "postal_code": "94105",
        "country": "US"
    }
    checkout = await mcp._tool_manager.call_tool("update_customer_details", {"checkout_id": checkout_id, "address": address, "email": "john@example.com"})
    assert checkout.fulfillment is not None
    print("  Address and email updated successfully.")

    # 4. Start payment
    print("[Step 4] Starting payment...")
    checkout = await mcp._tool_manager.call_tool("start_payment", {"checkout_id": checkout_id})
    # If start_payment returns a string (error), this will fail, which is correct for a test
    assert not isinstance(checkout, str)
    assert checkout.status == "ready_for_complete"
    print("  Payment started. Status: ready_for_complete")

    # 5. Complete checkout
    print("[Step 5] Completing checkout...")
    checkout = await mcp._tool_manager.call_tool("complete_checkout", {"checkout_id": checkout_id})
    assert checkout.status == "completed"
    assert checkout.order is not None
    order_id = checkout.order.id
    print(f"  Order placed successfully! Order ID: {order_id}")

    # 6. Verify order resource
    print("[Step 6] Verifying order resource...")
    contents = await mcp.read_resource(f"ucp://orders/{order_id}")
    order_data = json.loads(contents[0].content)
    assert order_data["order"]["id"] == order_id
    print("  Order resource verified.")

@pytest.mark.asyncio
async def test_resources():
    # Test catalog resource
    contents = await mcp.read_resource("ucp://catalog/products")
    catalog_data = json.loads(contents[0].content)
    assert len(catalog_data["results"]) > 0

    # Test discovery profile resource
    contents = await mcp.read_resource("ucp://discovery/profile")
    profile = json.loads(contents[0].content)
    assert "ucp" in profile
    assert "capabilities" in profile["ucp"]

@pytest.mark.asyncio
async def test_checkout_management():
    # Create checkout
    results = await mcp._tool_manager.call_tool("search_shopping_catalog", {"query": ""})
    p1 = results.results[0].product_id
    p2 = results.results[1].product_id

    checkout = await mcp._tool_manager.call_tool("add_to_checkout", {"product_id": p1, "quantity": 1})
    checkout_id = checkout.id

    # Add another product
    checkout = await mcp._tool_manager.call_tool("add_to_checkout", {"product_id": p2, "quantity": 1, "checkout_id": checkout_id})
    assert len(checkout.line_items) == 2

    # Update quantity
    checkout = await mcp._tool_manager.call_tool("update_checkout", {"checkout_id": checkout_id, "product_id": p1, "quantity": 5})
    for li in checkout.line_items:
        if li.item.id == p1:
            assert li.quantity == 5

    # Remove item
    checkout = await mcp._tool_manager.call_tool("remove_from_checkout", {"checkout_id": checkout_id, "product_id": p2})
    assert len(checkout.line_items) == 1
    assert checkout.line_items[0].item.id == p1

    # Get checkout tool
    checkout_state = await mcp._tool_manager.call_tool("get_checkout", {"checkout_id": checkout_id})
    assert checkout_state.id == checkout_id

    # Get checkout resource
    contents = await mcp.read_resource(f"ucp://checkout/{checkout_id}")
    checkout_resource_data = json.loads(contents[0].content)
    assert checkout_resource_data["id"] == checkout_id

# UCP Shopping Service - MCP Server

A robust Model Context Protocol (MCP) server that provides access to Universal Commerce Protocol (UCP) shopping capabilities. This server enables AI agents to browse catalogs, manage checkouts, and complete purchases using a standardized interface.

## 🏗️ Architecture

The following diagram illustrates the shopping flow implemented by the UCP MCP Server:

```mermaid
sequenceDiagram
    participant User
    participant Agent
    participant MCP as UCP MCP Server
    participant Store as Retail Store

    User->>Agent: "Find chocochip cookies"
    Agent->>MCP: call search_shopping_catalog("cookies")
    MCP->>Store: search_products("cookies")
    Store-->>MCP: ProductResults
    MCP-->>Agent: Product list
    Agent-->>User: "Found Chocochip Cookies"

    User->>Agent: "Add 2 to my cart"
    Agent->>MCP: call add_to_checkout(BISC-001, 2)
    MCP->>Store: create / update checkout
    Store-->>MCP: Checkout Object
    MCP-->>Agent: Checkout ID & Details

    User->>Agent: "Ship it to 123 Main St"
    Agent->>MCP: call update_customer_details(addr, email)
    MCP->>Store: add_delivery_address()
    Store-->>MCP: Updated Checkout

    Note over Agent, MCP: Agent reviews state via ucp://checkout/{id}

    User->>Agent: "Complete the purchase"
    Agent->>MCP: call complete_checkout(id)
    MCP->>Store: place_order(id)
    Store-->>MCP: Completed Checkout / Order ID
    MCP-->>Agent: Success & Order ID
    Agent-->>User: "Order ORD-123 placed!"
```

## 🛠️ MCP Tools

| Tool Name | Description | Arguments |
|-----------|-------------|-----------|
| `search_shopping_catalog` | Search for products. Returns all if query is empty. | `query` (string) |
| `add_to_checkout` | Adds product to cart. Creates checkout if `checkout_id` missing. | `product_id`, `quantity`, `checkout_id` |
| `remove_from_checkout` | Removes a product from a specific checkout. | `checkout_id`, `product_id` |
| `update_checkout` | Updates item quantity in an existing checkout. | `checkout_id`, `product_id`, `quantity` |
| `get_checkout` | Retrieves the current state of a checkout. | `checkout_id` |
| `start_payment` | Initiates the payment process for a checkout. | `checkout_id` |
| `update_customer_details` | Sets shipping address and buyer email. | `checkout_id`, `address` (dict), `email` |
| `complete_checkout` | Finalizes the checkout and places the order. | `checkout_id` |

## 📄 MCP Resources

| Resource URI | Description |
|--------------|-------------|
| `ucp://catalog/products` | The complete product catalog. |
| `ucp://discovery/profile` | Merchant's UCP capability profile. |
| `ucp://checkout/{checkout_id}` | Live state of a specific checkout session. |
| `ucp://orders/{order_id}` | Order confirmation details for a completed purchase. |

## 💬 MCP Prompts

- **`shopping_assistance`**: A persona-driven prompt that guides the agent on how to use the UCP Shopping Service to help users find and buy products.

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- `uv` package manager

### Installation

```bash
# Install dependencies
uv sync
```

### Running the Server

**Standard I/O (Stdio):**
```bash
PYTHONPATH=. uv run python -m src.mcp_ucp_server --transport stdio
```

**Server-Sent Events (SSE):**
```bash
PYTHONPATH=. uv run python -m src.mcp_ucp_server --transport sse --port 8001
```

### Running the Demo Client

A polished demonstration script is provided to walk through a complete "happy path" shopping journey:

```bash
# Run stdio demo
PYTHONPATH=. uv run python mcp_ucp_client.py

# Run against a live SSE server
PYTHONPATH=. uv run python mcp_ucp_client.py --transport http --url http://localhost:8001/sse
```

## 🧪 Testing

Run the comprehensive test suite (including end-to-end integration tests):

```bash
PYTHONPATH=. uv run pytest tests/test_mcp_ucp_server.py -v
```

## 📜 License

Copyright 2026 UCP Authors. Licensed under the Apache License, Version 2.0.

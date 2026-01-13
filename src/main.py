import argparse
import logging
import uvicorn
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.applications import Starlette

from .mcp_ucp_server import mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
        from mcp.server.transport_security import TransportSecuritySettings
        
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        # Disable DNS rebinding protection for the ALB
        mcp.settings.transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
        
        # Get the Starlette app from FastMCP
        app = mcp.streamable_http_app()
        
        # Add a health check route for the ALB
        @app.route("/")
        async def health_check(request):
            return JSONResponse({"status": "ok"})
            
        logger.info(f"Starting Streamable HTTP server on {args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
    elif args.transport == "sse":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="sse")


if __name__ == "__main__":
    main()

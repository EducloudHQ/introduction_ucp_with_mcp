import os
import json
import base64
import requests
import logging
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

# Configuration from environment or hardcoded (for this tutorial)
GATEWAY_URL = "https://ucp-mcp-gateway-z5trhq8nqn.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
COGNITO_DOMAIN = "agentcore-b892d794.auth.us-east-1.amazoncognito.com"
CLIENT_ID = "39tsk8a4eahahjh1bft1dqv474"
CLIENT_SECRET = "18bknlmu58g64h8alb0aip1krdnecqmhebss7bo75c1gaf9se58q"
SCOPE = "ucp-mcp-gateway/invoke"

def get_access_token():
    """Obtain JWT access token from Cognito for the Gateway."""
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "scope": SCOPE
    }
    token_url = f"https://{COGNITO_DOMAIN}/oauth2/token"
    
    response = requests.post(token_url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

@app.entrypoint
def invoke(payload, context):
    """Entry point for AgentCore Runtime."""
    prompt = payload.get("prompt", "What tools do you have?")
    logger.info(f"Invoking agent with prompt: {prompt}")

    # Initialize model
    bedrock_model = BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        region_name='us-east-1',
        temperature=0.3,
    )

    # Get token for Gateway
    token = get_access_token()
    
    # Create MCP client pointing to the Gateway
    mcp_client = MCPClient(
        lambda: streamablehttp_client(
            GATEWAY_URL, 
            headers={"Authorization": f"Bearer {token}"}
        )
    )

    with mcp_client:
        # List tools via Gateway (this also triggers synchronization if needed)
        tools = mcp_client.list_tools_sync()
        logger.info(f"Discovered {len(tools)} tools via Gateway")

        # Create Strands agent
        agent = Agent(model=bedrock_model, tools=tools)

        # Run the agent
        response = agent(prompt)
        
        return {"result": str(response)}

if __name__ == "__main__":
    app.run()
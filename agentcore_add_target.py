import boto3
import json
import os

REGION = 'us-east-1'
GATEWAY_ID = 'ucp-mcp-gateway-z5trhq8nqn'
MCP_ENDPOINT = 'https://uc-ce1a9f9e45db4b6cb6688cec3237b10c.ecs.us-east-1.on.aws/mcp'

def add_mcp_target():
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    print(f"Adding MCP target {MCP_ENDPOINT} to gateway {GATEWAY_ID}...")
    
    try:
        response = client.create_gateway_target(
            name='ucp-mcp-target',
            gatewayIdentifier=GATEWAY_ID,
            targetConfiguration={
                'mcp': {
                    'mcpServer': {
                        'endpoint': MCP_ENDPOINT
                    }
                }
            }
        )
        print("Successfully added MCP target!")
        print(json.dumps(response, indent=2, default=str))
    except Exception as e:
        print(f"Error adding target: {e}")

if __name__ == "__main__":
    add_mcp_target()

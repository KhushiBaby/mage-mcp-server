#!/usr/bin/env python

"""
Mage.ai MCP Server Entrypoint

This script initializes and runs the MageMCP server to provide
an interface between Mage.ai and AI assistants via MCP.
"""

import os
import argparse
from dotenv import load_dotenv
from mage_mcp.server import MageMCP

# Setup argument parser
parser = argparse.ArgumentParser(description="Run the Mage.ai MCP Server")
parser.add_argument(
    "--api-url", 
    help="Mage.ai API URL (default: http://localhost:6789/api/)",
    default=os.environ.get("MAGE_API_URL", "http://localhost:6789/api/")
)
parser.add_argument(
    "--api-key", 
    help="Mage.ai API Key",
    default=os.environ.get("MAGE_API_KEY", "")
)
parser.add_argument(
    "--debug", 
    help="Enable debug logging", 
    action="store_true"
)
parser.add_argument(
    "--transport", 
    help="MCP transport protocol (stdio or sse)", 
    choices=["stdio", "sse"],
    default="stdio"
)
parser.add_argument(
    "--host", 
    help="Host for SSE transport (default: localhost)",
    default="localhost"
)
parser.add_argument(
    "--port", 
    help="Port for SSE transport (default: 3000)",
    type=int,
    default=3000
)

if __name__ == "__main__":
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Parse command line arguments
    args = parser.parse_args()
    
    # Set environment variables based on arguments
    os.environ["MAGE_API_URL"] = args.api_url
    os.environ["MAGE_API_KEY"] = args.api_key
    
    # Set up logging
    if args.debug:
        os.environ["LOG_LEVEL"] = "DEBUG"
    
    # Initialize and run the MCP server
    mage_mcp = MageMCP("Mage.ai MCP")
    
    # Run with specified transport
    if args.transport == "sse":
        mage_mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mage_mcp.run(transport="stdio")

#!/usr/bin/env python

"""
Development script for quick testing of the Mage.ai MCP server.

This script sets up a development environment for testing both the mock API server
and the MCP server simultaneously.
"""

import os
import sys
import argparse
import subprocess
import threading
import time
from pathlib import Path

# Ensure the package root is in the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def run_mock_server(port):
    """Run the mock Mage.ai API server."""
    mock_server_path = Path(__file__).parent / "tests" / "mock_api_server.py"
    print(f"Starting mock Mage.ai API server on port {port}...")
    mock_process = subprocess.Popen(
        [sys.executable, str(mock_server_path), "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return mock_process

def run_mcp_server(api_port, transport="stdio", sse_port=None):
    """Run the MCP server."""
    # Set environment variable for the mock API
    os.environ["MAGE_API_URL"] = f"http://localhost:{api_port}/api/"
    
    from mage_mcp.server import MageMCP
    
    print(f"Starting Mage.ai MCP server (transport: {transport})...")
    mcp_server = MageMCP("Mage.ai MCP Dev")
    
    if transport == "sse" and sse_port:
        mcp_server.run(transport="sse", host="localhost", port=sse_port)
    else:
        mcp_server.run(transport="stdio")

def main():
    """Entry point for development testing."""
    parser = argparse.ArgumentParser(description="Run Mage.ai MCP development environment")
    parser.add_argument("--api-port", type=int, default=6789, help="Port for mock Mage.ai API server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="MCP transport protocol")
    parser.add_argument("--sse-port", type=int, default=3000, help="Port for SSE transport")
    parser.add_argument("--no-mock", action="store_true", help="Don't start the mock API server")
    args = parser.parse_args()
    
    # Start the mock API server if requested
    mock_process = None
    if not args.no_mock:
        mock_process = run_mock_server(args.api_port)
        # Small delay to ensure the mock server is up
        time.sleep(1)
    
    try:
        # Start the MCP server
        run_mcp_server(args.api_port, args.transport, args.sse_port)
    finally:
        # Clean up the mock server if it's running
        if mock_process:
            print("Shutting down mock API server...")
            mock_process.terminate()
            mock_process.wait()

if __name__ == "__main__":
    main()

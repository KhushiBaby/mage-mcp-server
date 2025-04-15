#!/usr/bin/env python

"""
Test script for Mage.ai MCP server.

This script contains tests to verify the functionality of the MageMCP server.
"""

import os
import unittest
from unittest.mock import Mock, patch
import json
import sys
import httpx

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mage_mcp.server.mage_mcp_server import MageMCP, MageAPIClient


class MockResponse:
    """Mock HTTP response for testing."""
    
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "Mock HTTP Error", 
                request=httpx.Request("GET", "http://test.com"), 
                response=self
            )


class TestMageAPIClient(unittest.TestCase):
    """Test the MageAPIClient class."""
    
    @patch('httpx.Client.get')
    def test_get_request(self, mock_get):
        """Test that get requests work correctly."""
        mock_get.return_value = MockResponse({"test": "data"})
        
        client = MageAPIClient()
        result = client.request("test_endpoint")
        
        mock_get.assert_called_once()
        self.assertEqual(result, {"test": "data"})
    
    @patch('httpx.Client.post')
    def test_post_request(self, mock_post):
        """Test that post requests work correctly."""
        mock_post.return_value = MockResponse({"result": "success"})
        
        client = MageAPIClient()
        result = client.request("test_endpoint", method="POST", payload={"data": "test"})
        
        mock_post.assert_called_once()
        self.assertEqual(result, {"result": "success"})
    
    @patch('httpx.Client.get')
    def test_error_handling(self, mock_get):
        """Test error handling in requests."""
        mock_get.return_value = MockResponse({"error": "Not found"}, 404)
        
        client = MageAPIClient()
        with self.assertRaises(RuntimeError):
            client.request("nonexistent_endpoint")


class TestMageMCP(unittest.TestCase):
    """Test the MageMCP server."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock MCP for testing
        self.mcp_mock = Mock()
        
        # Create patches
        self.fast_mcp_patch = patch('mage_mcp.server.mage_mcp_server.FastMCP', return_value=self.mcp_mock)
        
        # Start patches
        self.fast_mcp_mock = self.fast_mcp_patch.start()
        
    def tearDown(self):
        """Clean up after tests."""
        # Stop patches
        self.fast_mcp_patch.stop()
    
    def test_initialization(self):
        """Test that the server initializes correctly."""
        mage_mcp = MageMCP()
        
        # Check that FastMCP was instantiated
        self.fast_mcp_mock.assert_called_once()
        
        # Check that handlers were set up
        self.mcp_mock.resource.assert_called()
        self.mcp_mock.tool.assert_called()


if __name__ == '__main__':
    unittest.main()

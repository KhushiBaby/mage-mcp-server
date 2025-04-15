#!/usr/bin/env python

"""
Mock Mage.ai API Server for testing the MCP client.

This script creates a local HTTP server that mimics the Mage.ai API
responses for testing the MCP client without an actual Mage.ai instance.
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import argparse
import time
from urllib.parse import urlparse, parse_qs

# Sample data for mock responses
SAMPLE_DATA = {
    "pipelines": [
        {
            "uuid": "example_pipeline",
            "name": "Example Pipeline",
            "description": "A sample pipeline for testing",
            "type": "python",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z"
        },
        {
            "uuid": "data_processing",
            "name": "Data Processing",
            "description": "Pipeline for processing raw data",
            "type": "python",
            "created_at": "2023-02-01T00:00:00Z",
            "updated_at": "2023-02-02T00:00:00Z"
        }
    ],
    "blocks": {
        "example_pipeline": [
            {
                "uuid": "data_loader",
                "name": "Load Data",
                "type": "data_loader",
                "language": "python",
                "status": "not_executed",
                "content": "# Data loader block\n\n@data_loader\ndef load_data():\n    # Load data from source\n    data = {\n        'column1': [1, 2, 3],\n        'column2': ['a', 'b', 'c']\n    }\n    return data"
            },
            {
                "uuid": "transformer",
                "name": "Transform Data",
                "type": "transformer",
                "language": "python",
                "status": "not_executed",
                "content": "# Transformer block\n\n@transformer\ndef transform(data, *args, **kwargs):\n    # Transform the data\n    data['column3'] = [x * 2 for x in data['column1']]\n    return data"
            },
            {
                "uuid": "data_exporter",
                "name": "Export Data",
                "type": "data_exporter",
                "language": "python", 
                "status": "not_executed",
                "content": "# Data exporter block\n\n@data_exporter\ndef export_data(data, *args, **kwargs):\n    # Export the data\n    print(f'Exporting data with columns: {list(data.keys())}')\n    return data"
            }
        ],
        "data_processing": [
            {
                "uuid": "ingest_csv",
                "name": "Ingest CSV",
                "type": "data_loader",
                "language": "python",
                "status": "not_executed",
                "content": "# CSV ingestion block\n\n@data_loader\ndef load_csv():\n    import pandas as pd\n    return pd.read_csv('sample_data.csv')"
            },
            {
                "uuid": "clean_data",
                "name": "Clean Data",
                "type": "transformer",
                "language": "python",
                "status": "not_executed",
                "content": "# Data cleaning block\n\n@transformer\ndef clean(df, *args, **kwargs):\n    # Remove duplicates\n    df = df.drop_duplicates()\n    # Drop rows with missing values\n    df = df.dropna()\n    return df"
            }
        ]
    }
}


class MockMageHandler(BaseHTTPRequestHandler):
    """Mock HTTP request handler for Mage.ai API."""
    
    def _set_headers(self, content_type="application/json"):
        """Set response headers."""
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()
    
    def _parse_request_body(self):
        """Parse JSON request body if present."""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            request_body = self.rfile.read(content_length)
            return json.loads(request_body)
        return {}
    
    def do_GET(self):
        """Handle GET requests."""
        url_parts = urlparse(self.path)
        path = url_parts.path
        query = parse_qs(url_parts.query)
        
        # Remove /api/ prefix if present
        if path.startswith("/api/"):
            path = path[5:]
        
        # List pipelines
        if path == "pipelines":
            self._set_headers()
            self.wfile.write(json.dumps({"pipelines": SAMPLE_DATA["pipelines"]}).encode())
        
        # Get pipeline details
        elif path.startswith("pipelines/") and "/blocks" not in path and "/content" not in path:
            pipeline_uuid = path.split("/")[1]
            pipeline = next((p for p in SAMPLE_DATA["pipelines"] if p["uuid"] == pipeline_uuid), None)
            
            if pipeline:
                self._set_headers()
                self.wfile.write(json.dumps({"pipeline": pipeline}).encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Pipeline not found"}).encode())
        
        # List pipeline blocks
        elif path.startswith("pipelines/") and path.endswith("/blocks"):
            pipeline_uuid = path.split("/")[1]
            
            if pipeline_uuid in SAMPLE_DATA["blocks"]:
                self._set_headers()
                self.wfile.write(json.dumps({"blocks": SAMPLE_DATA["blocks"][pipeline_uuid]}).encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Pipeline not found"}).encode())
        
        # Get block details
        elif "/blocks/" in path and not path.endswith("/content"):
            parts = path.split("/")
            pipeline_uuid = parts[1]
            block_uuid = parts[3]
            
            if pipeline_uuid in SAMPLE_DATA["blocks"]:
                block = next((b for b in SAMPLE_DATA["blocks"][pipeline_uuid] 
                              if b["uuid"] == block_uuid), None)
                
                if block:
                    self._set_headers()
                    self.wfile.write(json.dumps({"block": block}).encode())
                    return
            
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Block not found"}).encode())
        
        # Get block content
        elif "/blocks/" in path and path.endswith("/content"):
            parts = path.split("/")
            pipeline_uuid = parts[1]
            block_uuid = parts[3]
            
            if pipeline_uuid in SAMPLE_DATA["blocks"]:
                block = next((b for b in SAMPLE_DATA["blocks"][pipeline_uuid] 
                              if b["uuid"] == block_uuid), None)
                
                if block and "content" in block:
                    self._set_headers()
                    self.wfile.write(json.dumps({"content": block["content"]}).encode())
                    return
            
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Block content not found"}).encode())
        
        # Get pipeline content (custom endpoint)
        elif path.endswith("/content"):
            pipeline_uuid = path.split("/")[1]
            
            if pipeline_uuid in SAMPLE_DATA["blocks"]:
                content = f"# Pipeline: {pipeline_uuid}\n\n"
                for block in SAMPLE_DATA["blocks"][pipeline_uuid]:
                    content += f"## Block: {block['name']}\n"
                    content += f"Type: {block['type']}\n"
                    content += f"Language: {block['language']}\n\n"
                    content += block['content'] + "\n\n"
                    content += "=" * 40 + "\n\n"
                
                self._set_headers()
                self.wfile.write(json.dumps({"content": content}).encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Pipeline not found"}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests."""
        url_parts = urlparse(self.path)
        path = url_parts.path
        
        # Remove /api/ prefix if present
        if path.startswith("/api/"):
            path = path[5:]
        
        request_data = self._parse_request_body()
        
        # Create pipeline
        if path == "pipelines":
            pipeline_data = request_data.get("pipeline", {})
            new_pipeline = {
                "uuid": pipeline_data.get("name", "").lower().replace(" ", "_"),
                "name": pipeline_data.get("name", "Untitled"),
                "description": pipeline_data.get("description", ""),
                "type": pipeline_data.get("type", "python"),
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            
            SAMPLE_DATA["pipelines"].append(new_pipeline)
            SAMPLE_DATA["blocks"][new_pipeline["uuid"]] = []
            
            self._set_headers()
            self.wfile.write(json.dumps({"pipeline": new_pipeline}).encode())
        
        # Create block
        elif path.startswith("pipelines/") and path.endswith("/blocks"):
            pipeline_uuid = path.split("/")[1]
            
            if pipeline_uuid in SAMPLE_DATA["blocks"]:
                block_data = request_data.get("block", {})
                new_block = {
                    "uuid": block_data.get("name", "").lower().replace(" ", "_"),
                    "name": block_data.get("name", "Untitled"),
                    "type": block_data.get("type", "transformer"),
                    "language": block_data.get("language", "python"),
                    "status": "not_executed",
                    "content": block_data.get("content", "# Empty block")
                }
                
                SAMPLE_DATA["blocks"][pipeline_uuid].append(new_block)
                
                self._set_headers()
                self.wfile.write(json.dumps({"block": new_block}).encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Pipeline not found"}).encode())
        
        # Execute pipeline
        elif path == "pipeline_runs":
            pipeline_uuid = request_data.get("pipeline_run", {}).get("pipeline_uuid")
            
            if any(p["uuid"] == pipeline_uuid for p in SAMPLE_DATA["pipelines"]):
                self._set_headers()
                self.wfile.write(json.dumps({
                    "pipeline_run": {
                        "id": 12345,
                        "pipeline_uuid": pipeline_uuid,
                        "status": "running",
                        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }
                }).encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Pipeline not found"}).encode())
        
        # Execute block
        elif path == "block_runs":
            pipeline_uuid = request_data.get("block_run", {}).get("pipeline_uuid")
            block_uuid = request_data.get("block_run", {}).get("block_uuid")
            
            if pipeline_uuid in SAMPLE_DATA["blocks"]:
                block = next((b for b in SAMPLE_DATA["blocks"][pipeline_uuid] 
                              if b["uuid"] == block_uuid), None)
                
                if block:
                    self._set_headers()
                    self.wfile.write(json.dumps({
                        "block_run": {
                            "id": 67890,
                            "pipeline_uuid": pipeline_uuid,
                            "block_uuid": block_uuid,
                            "status": "running",
                            "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        }
                    }).encode())
                    return
            
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Block not found"}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())
    
    def do_PUT(self):
        """Handle PUT requests."""
        url_parts = urlparse(self.path)
        path = url_parts.path
        
        # Remove /api/ prefix if present
        if path.startswith("/api/"):
            path = path[5:]
        
        request_data = self._parse_request_body()
        
        # Update block
        if "/blocks/" in path:
            parts = path.split("/")
            pipeline_uuid = parts[1]
            block_uuid = parts[3]
            
            if pipeline_uuid in SAMPLE_DATA["blocks"]:
                for i, block in enumerate(SAMPLE_DATA["blocks"][pipeline_uuid]):
                    if block["uuid"] == block_uuid:
                        block_data = request_data.get("block", {})
                        
                        if "content" in block_data:
                            SAMPLE_DATA["blocks"][pipeline_uuid][i]["content"] = block_data["content"]
                        
                        if "name" in block_data:
                            SAMPLE_DATA["blocks"][pipeline_uuid][i]["name"] = block_data["name"]
                        
                        self._set_headers()
                        self.wfile.write(json.dumps({"block": SAMPLE_DATA["blocks"][pipeline_uuid][i]}).encode())
                        return
            
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Block not found"}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())


def run_server(port=6789):
    """Run the mock server on the specified port."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MockMageHandler)
    print(f"Starting mock Mage.ai API server on port {port}...")
    httpd.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a mock Mage.ai API server for testing")
    parser.add_argument("--port", type=int, default=6789, help="Port to run the server on")
    args = parser.parse_args()
    
    run_server(args.port)

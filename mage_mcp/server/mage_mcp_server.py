#!/usr/bin/env python

"""
MageMCP - MCP Server Implementation for Mage.ai

This module provides a Model Context Protocol (MCP) server for interacting with Mage.ai
data pipelines, making it easier for AI assistants to explore and manipulate
pipeline components.
"""

import os
import json
import httpx
from typing import Dict, List, Any, Optional, Union, Tuple
from urllib.parse import urljoin
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from collections.abc import AsyncIterator
import asyncio

from mcp.server.fastmcp import FastMCP, Context, Image

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MageAPIClient:
    """Handles communication with the Mage.ai API."""
    base_url: str = "http://localhost:6789/api/"
    api_key: Optional[str] = None
    client: Optional[httpx.Client] = None
    
    def __post_init__(self):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        
        self.client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=30.0
        )
    
    def request(self, endpoint: str, method: str = "GET", payload: Optional[Dict] = None) -> Dict[str, Any]:
        """Send a request to the Mage.ai API."""
        url = urljoin(self.base_url, endpoint)
        logger.info(f"Making {method} request to {url}")
        
        try:
            if method == "GET":
                response = self.client.get(url)
            elif method == "POST":
                response = self.client.post(url, json=payload)
            elif method == "PUT":
                response = self.client.put(url, json=payload)
            elif method == "DELETE":
                response = self.client.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            try:
                error_message = e.response.json()
                logger.error(f"Error details: {error_message}")
            except:
                error_message = {"error": str(e)}
            
            raise RuntimeError(f"Error communicating with Mage.ai API: {str(e)}")
        except Exception as e:
            logger.error(f"Error during API request: {str(e)}")
            raise RuntimeError(f"Failed to communicate with Mage.ai: {str(e)}")


@dataclass
class MageContext:
    """Application context for the MageMCP server."""
    api_client: MageAPIClient


@asynccontextmanager
async def mage_lifespan(server: FastMCP) -> AsyncIterator[MageContext]:
    """Manage the lifecycle of the MageMCP server."""
    # Initialize the Mage.ai API client
    base_url = os.getenv("MAGE_API_URL", "http://localhost:6789/api/")
    api_key = os.getenv("MAGE_API_KEY", "")
    
    api_client = MageAPIClient(base_url=base_url, api_key=api_key)
    
    try:
        yield MageContext(api_client=api_client)
    finally:
        # Clean up resources if needed
        if api_client.client:
            api_client.client.close()


class MageMCP:
    """MCP Server for Mage.ai."""
    
    def __init__(self, name: str = "Mage.ai MCP"):
        """Initialize the MageMCP server.
        
        Args:
            name: Name of the MCP server
        """
        self.mcp = FastMCP(name, lifespan=mage_lifespan)
        self._setup_resources()
        self._setup_tools()
    
    def _setup_resources(self):
        """Set up resource handlers."""
        # Pipeline resources
        self.mcp.resource("mage://pipelines")(self.list_pipelines)
        self.mcp.resource("mage://pipelines/{pipeline_uuid}")(self.get_pipeline_details)
        self.mcp.resource("mage://pipelines/{pipeline_uuid}/blocks")(self.list_pipeline_blocks)
        self.mcp.resource("mage://pipelines/{pipeline_uuid}/blocks/{block_uuid}")(self.get_block_details)
        self.mcp.resource("mage://pipelines/{pipeline_uuid}/blocks/{block_uuid}/content")(self.get_block_content)
        self.mcp.resource("mage://pipelines/{pipeline_uuid}/content")(self.get_pipeline_content)
        self.mcp.resource("mage://pipelines/{pipeline_uuid}/execution")(self.get_pipeline_execution_details)
        self.mcp.resource("mage://blocks/search/{query}")(self.search_blocks)
        
    def _setup_tools(self):
        """Set up tool handlers."""
        # Pipeline management tools
        self.mcp.tool()(self.list_all_pipelines)
        self.mcp.tool()(self.get_pipeline_details)
        self.mcp.tool()(self.list_pipeline_blocks)
        self.mcp.tool()(self.get_block_content)
        self.mcp.tool()(self.create_pipeline)
        self.mcp.tool()(self.create_block)
        self.mcp.tool()(self.update_block_content)
        self.mcp.tool()(self.execute_pipeline)
        self.mcp.tool()(self.execute_block)
        self.mcp.tool()(self.get_pipeline_code)

    # === Resource Methods ===
    
    async def list_pipelines(self, ctx: Context) -> str:
        """Get a list of all pipelines from Mage.ai."""
        api_client = ctx.request_context.lifespan_context.api_client
        response = api_client.request("pipelines")
        pipelines = response.get("pipelines", [])
        return json.dumps(pipelines, indent=2)
    
    async def get_pipeline_details(self, pipeline_uuid: str, ctx: Context) -> str:
        """Get details for a specific pipeline by UUID."""
        api_client = ctx.request_context.lifespan_context.api_client
        response = api_client.request(f"pipelines/{pipeline_uuid}")
        return json.dumps(response, indent=2)
    
    async def list_pipeline_blocks(self, pipeline_uuid: str, ctx: Context) -> str:
        """List all blocks in a pipeline."""
        api_client = ctx.request_context.lifespan_context.api_client
        response = api_client.request(f"pipelines/{pipeline_uuid}/blocks")
        blocks = response.get("blocks", [])
        return json.dumps(blocks, indent=2)
    
    async def get_block_details(self, pipeline_uuid: str, block_uuid: str, ctx: Context) -> str:
        """Get details for a specific block in a pipeline."""
        api_client = ctx.request_context.lifespan_context.api_client
        response = api_client.request(f"pipelines/{pipeline_uuid}/blocks/{block_uuid}")
        return json.dumps(response, indent=2)
    
    async def get_block_content(self, pipeline_uuid: str, block_uuid: str, ctx: Context) -> str:
        """Get the code content of a specific block."""
        api_client = ctx.request_context.lifespan_context.api_client
        response = api_client.request(f"pipelines/{pipeline_uuid}/blocks/{block_uuid}/content")
        content = response.get("content", "No content found")
        return content
    
    async def get_pipeline_content(self, pipeline_uuid: str, ctx: Context) -> str:
        """Get the entire content of a pipeline including all blocks."""
        api_client = ctx.request_context.lifespan_context.api_client
        
        # First, get pipeline details
        pipeline_response = api_client.request(f"pipelines/{pipeline_uuid}")
        pipeline = pipeline_response.get("pipeline", {})
        
        # Then, get all blocks
        blocks_response = api_client.request(f"pipelines/{pipeline_uuid}/blocks")
        blocks = blocks_response.get("blocks", [])
        
        # Format the pipeline content
        content = f"# Pipeline: {pipeline.get('name')}\n"
        content += f"# UUID: {pipeline.get('uuid')}\n"
        content += f"# Description: {pipeline.get('description') or 'No description'}\n"
        content += f"# Type: {pipeline.get('type')}\n\n"
        
        # Get content for each block
        for block in blocks:
            block_uuid = block.get("uuid")
            block_name = block.get("name")
            block_type = block.get("type")
            
            try:
                block_content_response = api_client.request(
                    f"pipelines/{pipeline_uuid}/blocks/{block_uuid}/content"
                )
                block_content = block_content_response.get("content", "# No content found")
                
                content += f"## Block: {block_name}\n"
                content += f"## Type: {block_type}\n"
                content += f"## UUID: {block_uuid}\n\n"
                content += block_content + "\n\n"
                content += "=" * 80 + "\n\n"
            except Exception as e:
                content += f"## Error retrieving content for block {block_name} ({block_uuid}): {str(e)}\n\n"
        
        return content
    
    async def get_pipeline_execution_details(self, pipeline_uuid: str, ctx: Context) -> str:
        """Get execution details for a pipeline."""
        api_client = ctx.request_context.lifespan_context.api_client
        
        try:
            # Get pipeline runs for this pipeline
            response = api_client.request(f"pipeline_runs?pipeline_uuid={pipeline_uuid}")
            pipeline_runs = response.get("pipeline_runs", [])
            
            if not pipeline_runs:
                return "No execution history found for this pipeline."
            
            result = f"Execution History for Pipeline {pipeline_uuid}:\n\n"
            
            for run in pipeline_runs:
                run_id = run.get("id")
                status = run.get("status")
                started_at = run.get("started_at")
                completed_at = run.get("completed_at") or "In progress"
                
                result += f"Run ID: {run_id}\n"
                result += f"Status: {status}\n"
                result += f"Started: {started_at}\n"
                result += f"Completed: {completed_at}\n"
                
                # Get block runs for this pipeline run
                block_runs_response = api_client.request(f"block_runs?pipeline_run_id={run_id}")
                block_runs = block_runs_response.get("block_runs", [])
                
                if block_runs:
                    result += "Block Executions:\n"
                    for block_run in block_runs:
                        block_name = block_run.get("block_name", "Unknown")
                        block_status = block_run.get("status")
                        block_uuid = block_run.get("block_uuid")
                        
                        result += f"  - {block_name} ({block_uuid}): {block_status}\n"
                
                result += "\n" + "-" * 40 + "\n\n"
            
            return result
        except Exception as e:
            return f"Error retrieving execution details: {str(e)}"
    
    async def search_blocks(self, query: str, ctx: Context) -> str:
        """Search for blocks across all pipelines."""
        api_client = ctx.request_context.lifespan_context.api_client
        
        try:
            # First, get all pipelines
            pipelines_response = api_client.request("pipelines")
            pipelines = pipelines_response.get("pipelines", [])
            
            results = []
            
            # For each pipeline, search through blocks
            for pipeline in pipelines:
                pipeline_uuid = pipeline.get("uuid")
                pipeline_name = pipeline.get("name")
                
                blocks_response = api_client.request(f"pipelines/{pipeline_uuid}/blocks")
                blocks = blocks_response.get("blocks", [])
                
                for block in blocks:
                    block_name = block.get("name", "")
                    block_uuid = block.get("uuid", "")
                    block_type = block.get("type", "")
                    
                    # If any of the fields match the query
                    if (query.lower() in block_name.lower() or 
                        query.lower() in block_uuid.lower() or
                        query.lower() in block_type.lower()):
                        
                        # Add block to results with pipeline info
                        results.append({
                            "pipeline_uuid": pipeline_uuid,
                            "pipeline_name": pipeline_name,
                            "block_uuid": block_uuid,
                            "block_name": block_name,
                            "block_type": block_type
                        })
                    else:
                        # If no metadata matches, check content
                        try:
                            content_response = api_client.request(
                                f"pipelines/{pipeline_uuid}/blocks/{block_uuid}/content"
                            )
                            content = content_response.get("content", "")
                            
                            if query.lower() in content.lower():
                                results.append({
                                    "pipeline_uuid": pipeline_uuid,
                                    "pipeline_name": pipeline_name,
                                    "block_uuid": block_uuid,
                                    "block_name": block_name,
                                    "block_type": block_type,
                                    "content_match": True
                                })
                        except Exception:
                            # Skip if content can't be retrieved
                            pass
            
            if not results:
                return f"No blocks found matching '{query}'."
            
            formatted_results = f"Found {len(results)} blocks matching '{query}':\n\n"
            
            for idx, result in enumerate(results, 1):
                formatted_results += f"{idx}. Pipeline: {result['pipeline_name']} ({result['pipeline_uuid']})\n"
                formatted_results += f"   Block: {result['block_name']} ({result['block_uuid']})\n"
                formatted_results += f"   Type: {result['block_type']}\n"
                if result.get("content_match"):
                    formatted_results += f"   Note: Query matched in block content\n"
                formatted_results += "\n"
            
            return formatted_results
        except Exception as e:
            return f"Error searching blocks: {str(e)}"

    # === Tool Methods ===
    
    async def list_all_pipelines(self) -> str:
        """List all pipelines in Mage.ai with their basic details."""
        try:
            # Use the Context to get the API client
            ctx = self.mcp.get_current_context()
            api_client = ctx.request_context.lifespan_context.api_client
            
            response = api_client.request("pipelines")
            pipelines = response.get("pipelines", [])
            
            if not pipelines:
                return "No pipelines found in Mage.ai."
            
            result = "Available Pipelines in Mage.ai:\n\n"
            for idx, pipeline in enumerate(pipelines, 1):
                result += f"{idx}. {pipeline.get('name', 'Unnamed')} (UUID: {pipeline.get('uuid', 'N/A')})\n"
                result += f"   Description: {pipeline.get('description') or 'No description'}\n"
                result += f"   Type: {pipeline.get('type', 'N/A')}\n"
                result += f"   Created: {pipeline.get('created_at', 'N/A')}\n\n"
            
            return result
        except Exception as e:
            logger.error(f"Error in list_all_pipelines: {str(e)}")
            return f"Error listing pipelines: {str(e)}"
    
    async def get_pipeline_details(self, pipeline_uuid: str) -> str:
        """Get detailed information about a specific pipeline."""
        try:
            ctx = self.mcp.get_current_context()
            api_client = ctx.request_context.lifespan_context.api_client
            
            response = api_client.request(f"pipelines/{pipeline_uuid}")
            
            pipeline = response.get("pipeline", {})
            if not pipeline:
                return f"No pipeline found with UUID: {pipeline_uuid}"
            
            result = f"Pipeline: {pipeline.get('name', 'Unnamed')}\n"
            result += f"UUID: {pipeline.get('uuid', 'N/A')}\n"
            result += f"Description: {pipeline.get('description') or 'No description'}\n"
            result += f"Type: {pipeline.get('type', 'N/A')}\n"
            result += f"Created at: {pipeline.get('created_at', 'N/A')}\n"
            result += f"Updated at: {pipeline.get('updated_at', 'N/A')}\n\n"
            
            # Get blocks information
            blocks_response = api_client.request(f"pipelines/{pipeline_uuid}/blocks")
            blocks = blocks_response.get("blocks", [])
            
            result += f"Total blocks: {len(blocks)}\n\n"
            
            if blocks:
                result += "Blocks:\n"
                for idx, block in enumerate(blocks, 1):
                    result += f"{idx}. {block.get('name', 'Unnamed')} (UUID: {block.get('uuid', 'N/A')})\n"
                    result += f"   Type: {block.get('type', 'N/A')}\n"
                    result += f"   Language: {block.get('language', 'N/A')}\n\n"
            
            return result
        except Exception as e:
            logger.error(f"Error in get_pipeline_details: {str(e)}")
            return f"Error getting pipeline details: {str(e)}"
    
    async def list_pipeline_blocks(self, pipeline_uuid: str) -> str:
        """List all blocks in a specific pipeline."""
        try:
            ctx = self.mcp.get_current_context()
            api_client = ctx.request_context.lifespan_context.api_client
            
            response = api_client.request(f"pipelines/{pipeline_uuid}/blocks")
            blocks = response.get("blocks", [])
            
            if not blocks:
                return f"No blocks found in pipeline with UUID: {pipeline_uuid}"
            
            result = f"Blocks in Pipeline (UUID: {pipeline_uuid}):\n\n"
            for idx, block in enumerate(blocks, 1):
                result += f"{idx}. {block.get('name', 'Unnamed')} (UUID: {block.get('uuid', 'N/A')})\n"
                result += f"   Type: {block.get('type', 'N/A')}\n"
                result += f"   Language: {block.get('language', 'N/A')}\n"
                result += f"   Status: {block.get('status', 'N/A')}\n\n"
            
            return result
        except Exception as e:
            logger.error(f"Error in list_pipeline_blocks: {str(e)}")
            return f"Error listing pipeline blocks: {str(e)}"
    
    async def get_block_content(self, pipeline_uuid: str, block_uuid: str) -> str:
        """Get the code content of a specific block in a pipeline."""
        try:
            ctx = self.mcp.get_current_context()
            api_client = ctx.request_context.lifespan_context.api_client
            
            # First get block details
            block_detail = api_client.request(f"pipelines/{pipeline_uuid}/blocks/{block_uuid}")
            block = block_detail.get("block", {})
            
            # Then get the content
            content_response = api_client.request(f"pipelines/{pipeline_uuid}/blocks/{block_uuid}/content")
            content = content_response.get("content", "No content available")
            
            result = f"Block: {block.get('name', 'Unnamed')}\n"
            result += f"Type: {block.get('type', 'N/A')}\n"
            result += f"Language: {block.get('language', 'N/A')}\n"
            result += f"Status: {block.get('status', 'N/A')}\n\n"
            result += "--- Content ---\n\n"
            result += content
            
            return result
        except Exception as e:
            logger.error(f"Error in get_block_content: {str(e)}")
            return f"Error getting block content: {str(e)}"
    
    async def create_pipeline(
        self, 
        name: str, 
        description: str = "", 
        pipeline_type: str = "python"
    ) -> str:
        """Create a new pipeline in Mage.ai."""
        try:
            ctx = self.mcp.get_current_context()
            api_client = ctx.request_context.lifespan_context.api_client
            
            payload = {
                "pipeline": {
                    "name": name,
                    "description": description,
                    "type": pipeline_type
                }
            }
            
            response = api_client.request("pipelines", method="POST", payload=payload)
            pipeline = response.get("pipeline", {})
            
            if not pipeline:
                return "Failed to create pipeline."
            
            result = "Pipeline created successfully:\n\n"
            result += f"Name: {pipeline.get('name')}\n"
            result += f"UUID: {pipeline.get('uuid')}\n"
            result += f"Description: {pipeline.get('description', 'No description')}\n"
            result += f"Type: {pipeline.get('type')}\n"
            
            return result
        except Exception as e:
            logger.error(f"Error in create_pipeline: {str(e)}")
            return f"Error creating pipeline: {str(e)}"
    
    async def create_block(
        self,
        pipeline_uuid: str, 
        name: str, 
        block_type: str, 
        language: str = "python",
        content: str = "",
        upstream_blocks: Optional[List[str]] = None
    ) -> str:
        """Create a new block in a pipeline."""
        try:
            ctx = self.mcp.get_current_context()
            api_client = ctx.request_context.lifespan_context.api_client
            
            if upstream_blocks is None:
                upstream_blocks = []
                
            payload = {
                "block": {
                    "name": name,
                    "type": block_type,
                    "language": language,
                    "content": content,
                    "upstream_blocks": upstream_blocks
                }
            }
            
            response = api_client.request(
                f"pipelines/{pipeline_uuid}/blocks", 
                method="POST", 
                payload=payload
            )
            
            block = response.get("block", {})
            
            if not block:
                return "Failed to create block."
            
            result = "Block created successfully:\n\n"
            result += f"Name: {block.get('name')}\n"
            result += f"UUID: {block.get('uuid')}\n"
            result += f"Type: {block.get('type')}\n"
            result += f"Language: {block.get('language')}\n"
            
            return result
        except Exception as e:
            logger.error(f"Error in create_block: {str(e)}")
            return f"Error creating block: {str(e)}"

    async def update_block_content(
        self,
        pipeline_uuid: str,
        block_uuid: str,
        content: str
    ) -> str:
        """Update the content of an existing block."""
        try:
            ctx = self.mcp.get_current_context()
            api_client = ctx.request_context.lifespan_context.api_client
            
            # First get block details to verify it exists
            block_detail = api_client.request(f"pipelines/{pipeline_uuid}/blocks/{block_uuid}")
            block = block_detail.get("block", {})
            
            if not block:
                return f"Block with UUID {block_uuid} not found in pipeline {pipeline_uuid}."
            
            # Update the block content
            payload = {
                "block": {
                    "content": content,
                    "name": block.get("name")  # Include name to maintain compatibility
                }
            }
            
            response = api_client.request(
                f"pipelines/{pipeline_uuid}/blocks/{block_uuid}",
                method="PUT",
                payload=payload
            )
            
            updated_block = response.get("block", {})
            
            if not updated_block:
                return "Failed to update block content."
            
            return f"Successfully updated content for block {updated_block.get('name')}."
        except Exception as e:
            logger.error(f"Error in update_block_content: {str(e)}")
            return f"Error updating block content: {str(e)}"

    async def execute_pipeline(self, pipeline_uuid: str) -> str:
        """Execute a pipeline."""
        try:
            ctx = self.mcp.get_current_context()
            api_client = ctx.request_context.lifespan_context.api_client
            
            # Trigger pipeline execution
            payload = {
                "pipeline_run": {
                    "pipeline_uuid": pipeline_uuid
                }
            }
            
            response = api_client.request("pipeline_runs", method="POST", payload=payload)
            pipeline_run = response.get("pipeline_run", {})
            
            if not pipeline_run:
                return "Failed to execute pipeline."
            
            pipeline_run_id = pipeline_run.get("id")
            
            result = f"Pipeline execution started:\n\n"
            result += f"Pipeline UUID: {pipeline_uuid}\n"
            result += f"Run ID: {pipeline_run_id}\n"
            result += f"Status: {pipeline_run.get('status', 'N/A')}\n"
            
            return result
        except Exception as e:
            logger.error(f"Error in execute_pipeline: {str(e)}")
            return f"Error executing pipeline: {str(e)}"

    async def execute_block(
        self,
        pipeline_uuid: str,
        block_uuid: str
    ) -> str:
        """Execute a single block in a pipeline."""
        try:
            ctx = self.mcp.get_current_context()
            api_client = ctx.request_context.lifespan_context.api_client
            
            # Execute the block
            payload = {
                "block_run": {
                    "pipeline_uuid": pipeline_uuid,
                    "block_uuid": block_uuid
                }
            }
            
            response = api_client.request("block_runs", method="POST", payload=payload)
            block_run = response.get("block_run", {})
            
            if not block_run:
                return "Failed to execute block."
            
            result = f"Block execution started:\n\n"
            result += f"Pipeline UUID: {pipeline_uuid}\n"
            result += f"Block UUID: {block_uuid}\n"
            result += f"Run ID: {block_run.get('id')}\n"
            result += f"Status: {block_run.get('status', 'N/A')}\n"
            
            return result
        except Exception as e:
            logger.error(f"Error in execute_block: {str(e)}")
            return f"Error executing block: {str(e)}"

    async def get_pipeline_code(self, pipeline_uuid: str) -> str:
        """Get the complete code of a pipeline including all blocks."""
        try:
            ctx = self.mcp.get_current_context()
            api_client = ctx.request_context.lifespan_context.api_client
            
            # Get pipeline details
            pipeline_response = api_client.request(f"pipelines/{pipeline_uuid}")
            pipeline = pipeline_response.get("pipeline", {})
            
            if not pipeline:
                return f"No pipeline found with UUID: {pipeline_uuid}"
            
            # Get all blocks for this pipeline
            blocks_response = api_client.request(f"pipelines/{pipeline_uuid}/blocks")
            blocks = blocks_response.get("blocks", [])
            
            # Format the pipeline code with metadata
            result = f"# Pipeline: {pipeline.get('name')}\n"
            result += f"# UUID: {pipeline.get('uuid')}\n"
            result += f"# Type: {pipeline.get('type')}\n"
            result += f"# Description: {pipeline.get('description') or 'No description'}\n\n"
            
            # Get block details and content
            for block in blocks:
                block_uuid = block.get("uuid")
                block_name = block.get("name", "Unnamed")
                block_type = block.get("type", "Unknown")
                language = block.get("language", "python")
                
                # Get block content
                content_response = api_client.request(f"pipelines/{pipeline_uuid}/blocks/{block_uuid}/content")
                content = content_response.get("content", "# No content available")
                
                # Format block
                result += f"# ===== Block: {block_name} =====\n"
                result += f"# Type: {block_type}\n"
                result += f"# Language: {language}\n"
                result += f"# UUID: {block_uuid}\n\n"
                
                # Language-specific formatting
                if language == "python":
                    result += f"'''\n{block_name} - {block_type}\n'''\n\n"
                elif language == "sql":
                    result += f"-- {block_name} - {block_type}\n\n"
                elif language == "r":
                    result += f"# {block_name} - {block_type}\n\n"
                
                result += f"{content}\n\n"
                result += "# " + "=" * 50 + "\n\n"
            
            return result
        except Exception as e:
            logger.error(f"Error in get_pipeline_code: {str(e)}")
            return f"Error retrieving pipeline code: {str(e)}"

    def run(self, **kwargs):
        """Run the MageMCP server."""
        self.mcp.run(**kwargs)


if __name__ == "__main__":
    # Initialize and run the MCP server
    mage_mcp = MageMCP()
    mage_mcp.run()

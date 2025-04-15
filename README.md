# Mage.ai MCP Integration

A comprehensive Model Context Protocol (MCP) integration for [Mage.ai](https://mage.ai/), allowing AI assistants like Anthropic's Claude to efficiently work with Mage data pipelines.

## Features

- **Browse Pipelines**: Explore all Mage.ai pipelines and their components
- **View and Edit Code**: Read and modify block code
- **Execute Pipelines**: Run entire pipelines or individual blocks
- **Search Functionality**: Find blocks by name, type, or content
- **Pipeline Creation**: Create new pipelines and blocks from scratch

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mage-mcp.git
cd mage-mcp

# Install dependencies
pip install -r requirements.txt
```

## Configuration

The server can be configured using environment variables or command-line arguments:

- `MAGE_API_URL`: URL for the Mage.ai API (default: `http://localhost:6789/api/`)
- `MAGE_API_KEY`: API key for authentication (if required)

Create a `.env` file for persistent configuration:

```
MAGE_API_URL=http://localhost:6789/api/
MAGE_API_KEY=your_api_key_if_needed
```

## Usage

### Running the Server

Use the provided script to start the MCP server:

```bash
# Using stdio transport (default)
python run_server.py

# Using SSE transport
python run_server.py --transport sse --host localhost --port 3000

# Additional options
python run_server.py --api-url http://your-mage-instance:6789/api/ --api-key your_key --debug
```

### Installing with Claude Desktop

For the best experience, install this server directly with Claude Desktop:

```bash
# Using mcp CLI
mcp install run_server.py --name "Mage.ai Manager"

# With environment variables
mcp install run_server.py -v MAGE_API_URL=http://localhost:6789/api/ -v MAGE_API_KEY=your_key
```

### Development Mode

For testing and development:

```bash
mcp dev run_server.py
```

## MCP Resources and Tools

### Resources

- `mage://pipelines` - List all pipelines
- `mage://pipelines/{pipeline_uuid}` - Get pipeline details
- `mage://pipelines/{pipeline_uuid}/blocks` - List blocks in a pipeline
- `mage://pipelines/{pipeline_uuid}/blocks/{block_uuid}` - Get block details
- `mage://pipelines/{pipeline_uuid}/blocks/{block_uuid}/content` - Get block code
- `mage://pipelines/{pipeline_uuid}/content` - Get entire pipeline content
- `mage://pipelines/{pipeline_uuid}/execution` - Get pipeline execution details
- `mage://blocks/search/{query}` - Search blocks by name, type or content

### Tools

- `list_all_pipelines()` - List all pipelines with details
- `get_pipeline_details(pipeline_uuid)` - Get pipeline information
- `list_pipeline_blocks(pipeline_uuid)` - List blocks in a pipeline
- `get_block_content(pipeline_uuid, block_uuid)` - Get block code
- `create_pipeline(name, description, pipeline_type)` - Create a new pipeline
- `create_block(pipeline_uuid, name, block_type, language, content, upstream_blocks)` - Create a block
- `update_block_content(pipeline_uuid, block_uuid, content)` - Update block code
- `execute_pipeline(pipeline_uuid)` - Run a pipeline
- `execute_block(pipeline_uuid, block_uuid)` - Run a specific block
- `get_pipeline_code(pipeline_uuid)` - Get complete pipeline code

## Example Interactions

```
User: Show me all the pipelines in Mage.ai.
Claude: Let me check what pipelines are available in your Mage.ai instance.

[Lists all pipelines with descriptions and types]

User: Can you show me the blocks in the data_ingestion pipeline?
Claude: Here are all the blocks in the data_ingestion pipeline:

[Lists all blocks with their types, languages, and status]

User: I need to modify the 'transform_data' block to fix a bug.
Claude: Let me help you with that. First, let's look at the current code:

[Shows the current block code]

Here's how we can fix the bug:
[Explains the issue and suggests changes]

Would you like me to update the block with these changes?

User: Yes, please update it.
Claude: I've updated the block. Here's the new content:

[Shows the updated code]

The changes have been saved successfully.
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

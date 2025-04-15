.PHONY: help install dev test lint format mock-server mcp-install

# Help command to show available commands
help:
	@echo "Mage.ai MCP Development Commands"
	@echo ""
	@echo "Usage:"
	@echo "  make install     Install the package and dependencies"
	@echo "  make dev         Run the development environment"
	@echo "  make test        Run tests"
	@echo "  make lint        Run linting"
	@echo "  make format      Format code"
	@echo "  make mock-server Run the mock Mage.ai API server"
	@echo "  make mcp-install Install the MCP server with Claude Desktop"
	@echo ""

# Install the package and dependencies
install:
	pip install -e ".[dev]"

# Run the development environment
dev:
	python dev.py

# Run tests
test:
	pytest

# Run linting
lint:
	flake8 mage_mcp
	mypy mage_mcp

# Format code
format:
	black mage_mcp tests
	isort mage_mcp tests

# Run the mock Mage.ai API server
mock-server:
	python tests/mock_api_server.py

# Install the MCP server with Claude Desktop
mcp-install:
	mcp install mage_mcp/run_server.py --name "Mage.ai Manager"

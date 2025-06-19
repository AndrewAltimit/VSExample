# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
VSExample is a containerized development environment that demonstrates Visual Studio Code integration with GitHub Actions using public runners. It provides MCP (Model Context Protocol) tools for C++ code quality checks, GitHub Actions workflow validation, and CI/CD pipeline execution.

## Common Commands

### Starting the Development Environment
```bash
# Start the MCP server in background
docker-compose up -d mcp-server

# Run Claude Code interface
./run_claude.sh
```

### Running Code Quality Checks
The project provides MCP tools that should be used instead of direct commands:
- Use `format_check` tool to check C++ code formatting
- Use `format_fix` tool to automatically fix formatting issues
- Use `lint` tool to run clang-tidy linting
- Use `analyze` tool for static analysis with cppcheck
- Use `full_ci` tool to run the complete CI pipeline

### GitHub Actions Management
- Use `check_workflow_runs` tool to monitor workflow status
- Use `validate_workflow_yaml` tool to validate workflow YAML syntax

## Architecture

### MCP Server (`mcp-server.py`)
The core of the project is a Python-based MCP server that exposes development tools through the Model Context Protocol. The server runs in a Docker container and provides tools for code formatting, linting, static analysis, and GitHub integration.

### Docker Setup
- **Base Image**: Ubuntu 22.04 with development tools
- **Service Name**: `mcp-server`
- **Working Directory**: `/workspace` (mounted from project root)
- **Key Dependencies**: Python 3, GitHub CLI, clang-format, clang-tidy, cppcheck
- **Port**: 8000 (exposed by container)

### Environment Requirements
- Docker and Docker Compose must be installed
- Node.js 22.16.0 (managed by NVM in `run_claude.sh`)
- GitHub token should be set as `GITHUB_TOKEN` environment variable for GitHub API access

## Development Workflow

1. **Code Changes**: Make changes to C++ source files in the project
2. **Format Check**: Use the `format_check` tool to verify formatting
3. **Auto-Format**: If needed, use `format_fix` to correct formatting
4. **Linting**: Run the `lint` tool to check for code issues
5. **Static Analysis**: Use `analyze` tool for deeper code analysis
6. **CI Pipeline**: Run `full_ci` to execute the complete pipeline before committing

## Important Notes

- All development tools run inside Docker containers for consistency
- The MCP server must be running (`docker-compose up -d mcp-server`) before using any tools
- Git configuration and SSH keys are automatically mounted from the host system
- The project is designed to work with public GitHub runners
- When working with GitHub Actions, ensure `GITHUB_TOKEN` is properly configured
#!/usr/bin/env python3
"""
MCP Server
Provides tools for Docker-based CI/CD pipeline, code quality checks, and testing.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server, InitializationOptions
from pydantic import AnyUrl


class MCPServer:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.server = Server("mcp-server")
        self._setup_tools()
        
    def _setup_tools(self):
        """Register all MCP tools."""
        
        # Code Quality Tools
        @self.server.call_tool()
        async def format_check(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Check C++ code formatting using clang-format."""
            return await self._run_docker_command(
                "format-check",
                "Checking C++ code formatting..."
            )
        
        @self.server.call_tool()
        async def format_fix(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Auto-fix C++ formatting issues using clang-format."""
            return await self._run_docker_command(
                "format-fix",
                "Auto-fixing C++ formatting..."
            )
        
        @self.server.call_tool()
        async def lint(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Run C++ linting using clang-tidy."""
            return await self._run_docker_command(
                "lint",
                "Running C++ linting checks..."
            )
        
        @self.server.call_tool()
        async def analyze(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Run static analysis on C++ code using cppcheck."""
            return await self._run_docker_command(
                "analyze",
                "Running static analysis..."
            )
        
        @self.server.call_tool()
        async def full_ci(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Execute complete CI pipeline."""
            return await self._run_docker_command(
                "ci",
                "Running complete CI pipeline...",
                timeout=600  # 10 minutes for full CI
            )
        
        # MCP Server
        @self.server.call_tool()
        async def start_dev_env(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Start containerized MCP server"""
            return await self._run_docker_command(
                "up mcp-server -d",
                "Starting MCP Server...",
                compose_command=True
            )
        
        @self.server.call_tool()
        async def stop_dev_env(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Stop MCP Server."""
            return await self._run_docker_command(
                "down",
                "Stopping MCP Server...",
                compose_command=True
            )
        
        # Utility Tools
        @self.server.call_tool()
        async def project_status(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Get current project status and Docker environment info."""
            return await self._get_project_status()
        
        # GitHub Actions monitoring tools
        @self.server.call_tool()
        async def check_workflow_runs(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Check GitHub Actions workflow runs and status."""
            limit = arguments.get('limit', 10)
            workflow_name = arguments.get('workflow_name', None)
            return await self._check_workflow_runs(limit, workflow_name)
        
        @self.server.call_tool()
        async def validate_workflow_yaml(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Validate GitHub Actions workflow YAML files for syntax errors."""
            workflow_file = arguments.get('workflow_file', None)
            return await self._validate_workflow_yaml(workflow_file)
    
    async def _check_workflow_runs(self, limit: int = 10, workflow_name: Optional[str] = None) -> List[types.TextContent]:
        """Check GitHub Actions workflow runs and status."""
        try:
            output_lines = []
            output_lines.append("🔍 GitHub Actions Workflow Status")
            output_lines.append("=" * 40)
            output_lines.append("")
            
            # Check GitHub authentication first
            auth_check = await self._check_github_auth()
            if not auth_check["authenticated"]:
                output_lines.extend(auth_check["messages"])
                return [types.TextContent(type="text", text="\n".join(output_lines))]
            
            # Use gh CLI to get workflow runs
            cmd = ["gh", "run", "list", "--limit", str(limit), "--json", 
                   "status,conclusion,name,createdAt,headBranch,workflowName,url,databaseId"]
            
            if workflow_name:
                cmd.extend(["--workflow", workflow_name])
            
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=str(self.project_root),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    if b"not found" in stderr or b"No workflows found" in stderr:
                        output_lines.append("ℹ️  No workflow runs found")
                        output_lines.append("💡 Check if this repository has GitHub Actions enabled")
                    else:
                        output_lines.append(f"❌ Error getting workflow runs: {stderr.decode()}")
                    return [types.TextContent(type="text", text="\n".join(output_lines))]
                
                import json
                runs = json.loads(stdout.decode())
                
                if not runs:
                    output_lines.append("ℹ️  No workflow runs found")
                    return [types.TextContent(type="text", text="\n".join(output_lines))]
                
                output_lines.append(f"📊 Latest {len(runs)} Workflow Runs:")
                output_lines.append("")
                
                for run in runs:
                    status = run.get('status', 'unknown')
                    conclusion = run.get('conclusion', 'unknown')
                    name = run.get('workflowName', 'Unknown')
                    branch = run.get('headBranch', 'unknown')
                    created = run.get('createdAt', '')
                    url = run.get('url', '')
                    run_id = run.get('databaseId', '')
                    
                    # Format status indicator
                    if status == 'completed':
                        if conclusion == 'success':
                            status_icon = "✅"
                        elif conclusion == 'failure':
                            status_icon = "❌"
                        elif conclusion == 'cancelled':
                            status_icon = "🚫"
                        else:
                            status_icon = "⚠️"
                    elif status == 'in_progress':
                        status_icon = "🔄"
                    elif status == 'queued':
                        status_icon = "⏳"
                    else:
                        status_icon = "❓"
                    
                    output_lines.append(f"{status_icon} **{name}** ({branch})")
                    output_lines.append(f"   Status: {status} | Conclusion: {conclusion}")
                    output_lines.append(f"   Created: {created[:19].replace('T', ' ')}")
                    output_lines.append(f"   Run ID: {run_id}")
                    if url:
                        output_lines.append(f"   URL: {url}")
                    output_lines.append("")
                
            except FileNotFoundError:
                output_lines.append("❌ GitHub CLI (gh) not found")
                output_lines.append("💡 Install GitHub CLI: https://cli.github.com/")
                output_lines.append("")
                output_lines.append("🔧 Alternative: Check workflows manually")
                output_lines.append("   Visit: https://github.com/your-repo/actions")
            
            return [types.TextContent(type="text", text="\n".join(output_lines))]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error checking workflow runs: {str(e)}"
            )]
    
    async def _check_github_auth(self) -> Dict[str, Any]:
        """Check GitHub CLI authentication status."""
        try:
            # Check if gh CLI is available
            process = await asyncio.create_subprocess_exec(
                "gh", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if process.returncode != 0:
                return {
                    "authenticated": False,
                    "messages": [
                        "❌ GitHub CLI not found",
                        "💡 Install GitHub CLI in container: included in Dockerfile",
                        "📚 Setup guide: ./scripts/setup-github-auth.sh"
                    ]
                }
            
            # Check authentication status
            process = await asyncio.create_subprocess_exec(
                "gh", "auth", "status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    "authenticated": True,
                    "messages": ["✅ GitHub CLI authenticated"]
                }
            else:
                messages = [
                    "❌ GitHub CLI not authenticated",
                    "🔧 Container setup:"
                ]
                
                # Check for GitHub token in environment
                import os
                if os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN'):
                    messages.extend([
                        "  1. GITHUB_TOKEN found in environment",
                        "  2. Run: echo $GITHUB_TOKEN | gh auth login --with-token"
                    ])
                else:
                    messages.extend([
                        "  1. Set GITHUB_TOKEN environment variable",
                        "  2. Run: docker-compose up -d mcp-server",
                        "  3. Or run: ./scripts/setup-github-auth.sh"
                    ])
                
                messages.extend([
                    "",
                    "🔑 Token requirements for private repos:",
                    "  - repo (full control of private repositories)",
                    "  - workflow (update GitHub Action workflows)",
                    "  - read:org (read org and team membership)"
                ])
                
                return {
                    "authenticated": False,
                    "messages": messages
                }
                
        except Exception as e:
            return {
                "authenticated": False,
                "messages": [
                    f"❌ Error checking GitHub auth: {str(e)}",
                    "💡 Run: ./scripts/setup-github-auth.sh"
                ]
            }
    
    async def _validate_workflow_yaml(self, workflow_file: Optional[str] = None) -> List[types.TextContent]:
        """Validate GitHub Actions workflow YAML files for syntax errors."""
        try:
            output_lines = []
            output_lines.append("🔍 GitHub Actions YAML Validation")
            output_lines.append("=" * 40)
            output_lines.append("")
            
            workflows_dir = self.project_root / ".github" / "workflows"
            if not workflows_dir.exists():
                output_lines.append("❌ No .github/workflows directory found")
                return [types.TextContent(type="text", text="\n".join(output_lines))]
            
            # Get workflow files to validate
            if workflow_file:
                workflow_files = [workflows_dir / workflow_file]
                if not workflow_files[0].exists():
                    output_lines.append(f"❌ Workflow file not found: {workflow_file}")
                    return [types.TextContent(type="text", text="\n".join(output_lines))]
            else:
                workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
            
            if not workflow_files:
                output_lines.append("ℹ️  No workflow files found")
                return [types.TextContent(type="text", text="\n".join(output_lines))]
            
            output_lines.append(f"📋 Validating {len(workflow_files)} workflow file(s):")
            output_lines.append("")
            
            import yaml
            
            all_valid = True
            for workflow_path in workflow_files:
                try:
                    with open(workflow_path, 'r') as f:
                        yaml_content = f.read()
                    
                    # Parse YAML to check syntax
                    yaml.safe_load(yaml_content)
                    
                    # Basic GitHub Actions structure validation
                    workflow_data = yaml.safe_load(yaml_content)
                    validation_errors = []
                    
                    # Check required fields
                    if 'on' not in workflow_data:
                        validation_errors.append("Missing 'on' trigger definition")
                    
                    if 'jobs' not in workflow_data:
                        validation_errors.append("Missing 'jobs' definition")
                    
                    # Check jobs structure
                    if 'jobs' in workflow_data:
                        jobs = workflow_data['jobs']
                        if not isinstance(jobs, dict):
                            validation_errors.append("'jobs' must be a dictionary")
                        else:
                            for job_name, job_data in jobs.items():
                                if not isinstance(job_data, dict):
                                    validation_errors.append(f"Job '{job_name}' must be a dictionary")
                                    continue
                                
                                if 'runs-on' not in job_data:
                                    validation_errors.append(f"Job '{job_name}' missing 'runs-on'")
                                
                                # Check container usage
                                if 'container' in job_data:
                                    container = job_data['container']
                                    if isinstance(container, dict) and 'image' not in container:
                                        validation_errors.append(f"Job '{job_name}' container missing 'image'")
                    
                    # Check for common issues in containerized workflows
                    yaml_str = yaml_content.lower()
                    if 'runs-on: self-hosted' in yaml_str and 'container:' not in yaml_str:
                        validation_errors.append("Self-hosted runner without container specification")
                    
                    if validation_errors:
                        output_lines.append(f"⚠️  {workflow_path.name}:")
                        for error in validation_errors:
                            output_lines.append(f"   - {error}")
                        all_valid = False
                    else:
                        output_lines.append(f"✅ {workflow_path.name}: Valid")
                    
                except yaml.YAMLError as e:
                    output_lines.append(f"❌ {workflow_path.name}: YAML syntax error")
                    output_lines.append(f"   Error: {str(e)}")
                    all_valid = False
                except Exception as e:
                    output_lines.append(f"❌ {workflow_path.name}: Validation error")
                    output_lines.append(f"   Error: {str(e)}")
                    all_valid = False
            
            output_lines.append("")
            if all_valid:
                output_lines.append("🎉 All workflow files are valid!")
            else:
                output_lines.append("⚠️  Some workflow files have issues that need attention")
            
            output_lines.append("")
            output_lines.append("💡 Helpful Commands:")
            output_lines.append("   - Check workflow runs: Use 'check_workflow_runs' MCP tool")
            output_lines.append("   - GitHub CLI: gh workflow list")
            output_lines.append("   - GitHub CLI: gh run list --workflow <name>")
            
            return [types.TextContent(type="text", text="\n".join(output_lines))]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error validating workflow YAML: {str(e)}"
            )]
    
    async def _run_docker_command(
        self, 
        command: str, 
        description: str,
        timeout: int = 300,
        compose_command: bool = False
    ) -> List[types.TextContent]:
        """Execute Docker command with proper error handling and formatting."""
        try:
            # Validate Docker environment
            if not await self._validate_docker_environment():
                return [types.TextContent(
                    type="text",
                    text="❌ Docker environment validation failed. Please ensure Docker is running and docker-compose.yml exists."
                )]
            
            # Build the command - use docker-compose exec for commands running inside containers
            if compose_command:
                cmd = ["docker-compose"] + command.split()
            else:
                # Use docker-compose run for one-off commands
                cmd = ["docker-compose", "run", "--rm", command]
            
            start_time = time.time()
            
            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return [types.TextContent(
                    type="text",
                    text=f"❌ Command timed out after {timeout} seconds: {' '.join(cmd)}"
                )]
            
            execution_time = time.time() - start_time
            
            # Format output
            output_lines = []
            output_lines.append(f"🚀 {description}")
            output_lines.append(f"📋 Command: {' '.join(cmd)}")
            output_lines.append(f"⏱️  Execution time: {execution_time:.2f}s")
            output_lines.append("")
            
            if process.returncode == 0:
                output_lines.append("✅ Success!")
                if stdout:
                    output_lines.append("📄 Output:")
                    output_lines.append(self._format_command_output(stdout.decode()))
            else:
                output_lines.append(f"❌ Failed with exit code {process.returncode}")
                if stderr:
                    output_lines.append("🔥 Error output:")
                    output_lines.append(self._format_error_output(stderr.decode()))
                if stdout:
                    output_lines.append("📄 Standard output:")
                    output_lines.append(self._format_command_output(stdout.decode()))
            
            return [types.TextContent(
                type="text",
                text="\n".join(output_lines)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error executing command: {str(e)}"
            )]
    
    async def _validate_docker_environment(self) -> bool:
        """Validate Docker environment and project structure."""
        try:
            # Check if docker-compose.yml exists
            compose_file = self.project_root / "docker-compose.yml"
            if not compose_file.exists():
                return False
            
            # Check if Docker daemon is running
            result = await asyncio.create_subprocess_exec(
                "docker", "ps",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            return result.returncode == 0
            
        except Exception:
            return False
    
    
    async def _validate_test_structure(self) -> List[types.TextContent]:
        """Validate test_cases/ directory structure and YAML files."""
        try:
            test_cases_dir = self.project_root / "test_cases"
            if not test_cases_dir.exists():
                return [types.TextContent(
                    type="text",
                    text="❌ test_cases/ directory not found"
                )]
            
            yaml_files = list(test_cases_dir.glob("*.yaml"))
            json_files = list(test_cases_dir.glob("*.json"))
            
            output_lines = []
            output_lines.append("🔍 Test Structure Validation")
            output_lines.append(f"📁 Directory: {test_cases_dir}")
            output_lines.append(f"📄 YAML files: {len(yaml_files)}")
            output_lines.append(f"📄 JSON files: {len(json_files)}")
            output_lines.append("")
            
            # Validate YAML files
            valid_yaml = []
            invalid_yaml = []
            
            for yaml_file in yaml_files:
                try:
                    with open(yaml_file, 'r') as f:
                        yaml.safe_load(f)
                    valid_yaml.append(yaml_file.name)
                except Exception as e:
                    invalid_yaml.append(f"{yaml_file.name}: {str(e)}")
            
            if valid_yaml:
                output_lines.append(f"✅ Valid YAML files ({len(valid_yaml)}):")
                for file in valid_yaml:
                    output_lines.append(f"  • {file}")
            
            if invalid_yaml:
                output_lines.append(f"❌ Invalid YAML files ({len(invalid_yaml)}):")
                for error in invalid_yaml:
                    output_lines.append(f"  • {error}")
            
            # Check for missing JSON counterparts
            missing_json = []
            for yaml_file in yaml_files:
                json_file = yaml_file.with_suffix('.json')
                if not json_file.exists():
                    missing_json.append(yaml_file.name)
            
            if missing_json:
                output_lines.append(f"⚠️  YAML files without JSON counterparts ({len(missing_json)}):")
                for file in missing_json:
                    output_lines.append(f"  • {file}")
            
            return [types.TextContent(
                type="text",
                text="\n".join(output_lines)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error validating test structure: {str(e)}"
            )]
    
    async def _get_project_status(self) -> List[types.TextContent]:
        """Get current project status and environment info."""
        try:
            output_lines = []
            output_lines.append("📊 Project Status")
            output_lines.append(f"📁 Project root: {self.project_root}")
            output_lines.append("")
            
            # Check Docker environment
            docker_status = await self._validate_docker_environment()
            output_lines.append(f"🐳 Docker: {'✅ Available' if docker_status else '❌ Not available'}")

            return [types.TextContent(
                type="text",
                text="\n".join(output_lines)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error getting project status: {str(e)}"
            )]
    
    def _format_command_output(self, output: str) -> str:
        """Format command output with syntax highlighting for C++ errors."""
        lines = output.strip().split('\n')
        formatted_lines = []
        
        for line in lines:
            # Highlight success messages
            if any(word in line.lower() for word in ['success', 'passed', 'complete']):
                formatted_lines.append(f"✅ {line}")
            elif any(word in line.lower() for word in ['warning']):
                formatted_lines.append(f"🟡 {line}")
            elif any(word in line.lower() for word in ['error']):
                formatted_lines.append(f"🔴 {line}")
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_error_output(self, output: str) -> str:
        """Format error output with highlighting."""
        lines = output.strip().split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip():
                formatted_lines.append(f"🔥 {line}")
        
        return '\n'.join(formatted_lines)
    
    def run(self):
        """Run the MCP server."""
        async def main():
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="mcp-server",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )
        
        asyncio.run(main())


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Server")
    parser.add_argument(
        "--project-root",
        type=str,
        help="Path to the project root directory"
    )
    
    args = parser.parse_args()
    
    server = MCPServer(args.project_root)
    server.run()
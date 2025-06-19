# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
VSExample is a learning exercise for migrating Visual Studio 2017 projects from Azure DevOps Server (TFS) to GitHub Actions using public Windows runners. The repository contains a .NET Framework 4.6.1 solution with a HelloWorld console application and MSTest unit tests.

## Common Commands

### Building the .NET Project Locally
```bash
# Restore NuGet packages
nuget restore VSExample.sln

# Build the solution
msbuild VSExample.sln /p:Configuration=Release /p:Platform="Any CPU"

# Run tests
vstest.console.exe HelloWorld.Tests\bin\Release\HelloWorld.Tests.dll
```

### Using GitHub CLI Tools
```bash
# Start the MCP server with GitHub CLI access
docker-compose up -d mcp-server

# Check workflow runs
docker-compose run --rm mcp-server gh workflow list --repo AndrewAltimit/VSExample
docker-compose run --rm mcp-server gh run list --repo AndrewAltimit/VSExample

# View specific workflow run details
docker-compose run --rm mcp-server gh run view <RUN_ID> --repo AndrewAltimit/VSExample
```

## Project Structure

### Solution Layout
- `VSExample.sln` - Visual Studio 2017 solution file (root directory)
- `HelloWorld/` - Main console application project
  - `HelloWorld.csproj` - .NET Framework 4.6.1 project file
  - `Program.cs` - Entry point with Hello World implementation
  - `Properties/AssemblyInfo.cs` - Assembly metadata
- `HelloWorld.Tests/` - MSTest unit test project
  - `HelloWorld.Tests.csproj` - Test project file
  - `UnitTest1.cs` - Basic unit tests
  - `packages.config` - NuGet package references

### GitHub Actions Workflows
- `.github/workflows/build.yml` - Simple build and test workflow
- `.github/workflows/tfs-style-build.yml` - Detailed workflow mimicking TFS build steps with:
  - Get Sources (checkout)
  - NuGet Restore
  - Visual Studio Build (MSBuild)
  - Visual Studio Test (VSTest)
  - Copy Files to Staging
  - Publish Artifacts

## GitHub Actions Configuration

### Windows Runner Requirements
- Uses `windows-latest` (or `windows-2022`) runners
- Requires MSBuild setup action: `microsoft/setup-msbuild@v1.1`
- Requires NuGet setup action: `NuGet/setup-nuget@v1.1.1`
- Requires VSTest setup action: `darenm/Setup-VSTest@v1.2`

### Build Variables (TFS-style)
- `BUILD_CONFIGURATION`: Release
- `BUILD_PLATFORM`: "Any CPU"
- `SOLUTION_FILE`: VSExample.sln

## Migration Notes from TFS

### Key Differences
1. **Build Agents**: TFS uses private build agents, GitHub Actions uses public runners
2. **Build Steps**: TFS tasks map to GitHub Actions as follows:
   - TFS "Get Sources" → `actions/checkout@v3`
   - TFS "NuGet Restore" → `nuget restore` command
   - TFS "Visual Studio Build" → `msbuild` command
   - TFS "Visual Studio Test" → `vstest.console.exe` command
   - TFS "Copy Files" → PowerShell `Copy-Item` commands
   - TFS "Publish Artifact" → `actions/upload-artifact@v3`

### Environment Setup
- The Docker container includes GitHub CLI for monitoring builds
- GITHUB_TOKEN must be configured in .env file for API access
- The container setup allows running gh commands to check workflow status

## Important Notes

- This is a .NET Framework 4.6.1 project (not .NET Core/5+)
- Visual Studio 2017 compatibility is maintained (ToolsVersion="15.0")
- MSTest is used for unit testing (not xUnit or NUnit)
- The project demonstrates migration patterns from TFS to GitHub Actions
- All builds run on Windows public runners to match typical TFS environments
# Azure DevOps Repository Discoverer

This Python script automatically discovers all repositories from Azure DevOps and adds them to gitopolis configuration with appropriate tags.

## Features

- 🔍 Discovers all repositories from Azure DevOps organization/project
- 🏷️ Tags repositories as "private" and "azuredevops" in gitopolis configuration
- 📝 Comprehensive logging to file and console
- 🚀 Uses Azure CLI (`az`) for secure authentication
- ⚡ Fast discovery without cloning (use `gitopolis clone` separately)
- 🛡️ Fail-fast error handling - stops immediately on any error to prevent data corruption

## Prerequisites

1. **Azure CLI (`az`)**: Must be installed and authenticated
   ```bash
   # Install Azure CLI (if not already installed)
   # On Ubuntu/Debian:
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

   # On macOS:
   brew install azure-cli

   # Authenticate with Azure DevOps
   az login
   az extension add --name azure-devops
   ```

## Installation

See the [main README](../README.md) for installation instructions.

## Usage

### Basic Usage

To discover all repositories from an organization and add them to gitopolis configuration:

```bash
python azure_devops_cloner.py --organization myorg --target ~/my-repos/.gitopolis.toml
```

### With Specific Project

To discover repositories from a specific project:

```bash
python azure_devops_cloner.py --organization myorg --project myproject --target ~/my-repos/.gitopolis.toml
```

## Command Line Options

| Option | Description | Required |
|--------|-------------|----------|
| `--organization` | Azure DevOps organization name | Yes |
| `--target`, `-t` | Path to .gitopolis.toml file | Yes |
| `--project` | Azure DevOps project name | No (defaults to all projects) |
| `--help` | Show help message | - |

## Troubleshooting

### "az: command not found"
Install Azure CLI following the instructions in Prerequisites.

### "az login" authentication issues
Run `az login` and follow the prompts to authenticate with your Azure account.

### Azure DevOps extension not found
Install the Azure DevOps extension: `az extension add --name azure-devops`

### Permission denied errors
Ensure you have:
- Access to the Azure DevOps organization/project

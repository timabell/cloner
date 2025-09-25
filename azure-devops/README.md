# Azure DevOps Repository Cloner

This Python script automatically clones all repositories from Azure DevOps and adds them to gitopolis (CLI tool) with appropriate tags.

> **Note**: This is part of a larger repository cloning project. See the [main README](../README.md) for setup instructions.

## Features

- 🔄 Clones all repositories from Azure DevOps organization/project
- 🏷️ Tags repositories as "private" (most Azure DevOps repos are private by default)
- 📝 Comprehensive logging to file and console
- 🚀 Uses Azure CLI (`az`) for secure authentication
- ⚡ Skips repositories that are already cloned locally
- 🛡️ Robust error handling and recovery

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

2. **Python 3.7+**: The script requires Python 3.7 or later

3. **Gitopolis CLI**: You'll need the gitopolis binary installed:
   - Download from [gitopolis releases](https://github.com/rustworkshop/gitopolis/releases)
   - Put the binary in your PATH

## Installation

See the [main README](../README.md) for installation instructions.

## Usage

### Basic Usage

To clone all repositories from an organization and add them to gitopolis:

```bash
python azure_devops_cloner.py --organization myorg --clone-dir ./repos
```

### With Specific Project

To clone repositories from a specific project:

```bash
python azure_devops_cloner.py --organization myorg --project myproject --clone-dir ./repos
```

### Full Example

```bash
python azure_devops_cloner.py --organization mycompany --project web-apps --clone-dir ~/my-repos
```

## Command Line Options

| Option | Description | Required |
|--------|-------------|----------|
| `--organization` | Azure DevOps organization name | Yes |
| `--clone-dir` | Directory where repositories will be cloned | Yes |
| `--project` | Azure DevOps project name | No (defaults to all projects) |
| `--help` | Show help message | - |

## How It Works

1. **Authentication Check**: Uses Azure CLI authentication (`az login`)
2. **Repository Discovery**: Uses `az repos list` to find all repositories in the organization/project
3. **Cloning**: Clones each repository using `git clone` with the repository's remote URL
4. **Gitopolis Integration**: Adds each repository to gitopolis with appropriate tags:
   - All repositories are tagged as "private" and "azuredevops"

## Logging

The script creates detailed logs in two places:
- **Console output**: Real-time progress and status updates
- **Log file**: `azure_devops_cloner.log` with detailed information for debugging

## Gitopolis CLI Integration

The script integrates with gitopolis by:

1. **Adding repositories**: Uses `gitopolis add <repo-name>` to add each cloned repository
2. **Tagging repositories**: Uses `gitopolis tag <tag> <repo-name>` to tag repositories with:
   - Visibility tag: "private" (hard-coded for Azure DevOps)
   - Source tag: "azuredevops"
3. **State management**: Creates/updates `.gitopolis.toml` file in the clone directory

## Error Handling

The script includes comprehensive error handling:
- **Network issues**: Retries and graceful degradation
- **Authentication problems**: Clear error messages with suggestions
- **File system errors**: Proper permissions checking
- **CLI failures**: Detailed logging of response codes and messages

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
- Write permissions to the clone directory

### Gitopolis CLI errors
- Ensure `gitopolis` binary is installed and in your PATH
- Check that you have write permissions in the clone directory
- Check the log file for detailed error messages

## Security Notes

- The script uses Azure CLI for authentication, which securely manages tokens
- No API keys or tokens are stored in the script
- SSH keys are used for cloning when available
- All API communications use HTTPS

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.

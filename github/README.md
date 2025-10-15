# GitHub Repository Discoverer

This Python script automatically discovers all your public and private GitHub repositories and adds them to gitopolis configuration with appropriate tags.

## Features

- 🔍 Discovers all public and private repositories from your GitHub account
- 🏷️ Tags repositories as "public", "private", or "internal" in gitopolis configuration
- 📝 Comprehensive logging to file and console
- 🚀 Uses GitHub CLI (`gh`) for secure authentication
- ⚡ Fast discovery without cloning (use `gitopolis clone` separately)
- 🛡️ Fail-fast error handling - stops immediately on any error to prevent data corruption

## Prerequisites

1. **GitHub CLI (`gh`)**: Must be installed and authenticated
   ```bash
   # Install gh (if not already installed)
   # On Ubuntu/Debian:
   sudo apt install gh

   # On macOS:
   brew install gh

   # Authenticate with GitHub
   gh auth login
   ```

## Installation

See the [main README](../README.md) for installation instructions.

## Usage

### Basic Usage

To discover all repositories from your authenticated user and add them to gitopolis configuration:

```bash
./github_cloner.py --target ~/my-repos/
# or
./github_cloner.py --target ~/my-repos/.gitopolis.toml
```

### With Owner (User or Organization)

To discover repositories from a specific user or organization:

```bash
./github_cloner.py --target ~/my-repos/ --owner mycompany
# or
./github_cloner.py --target ~/my-repos/.gitopolis.toml --owner mycompany
```

### Choosing Remote Protocol

By default, SSH URLs are used. To use HTTPS instead:

```bash
./github_cloner.py --target ~/my-repos/ --protocol https
```

### Adding to Existing Repositories

If a repository with the same name already exists in your config, the script will:
- Check if the URL already exists in any remote - if so, skip it
- If the URL is different, add it as a new remote with the specified name

By default, new remotes are named `origin`. You can customize this:

```bash
./github_cloner.py --target ~/my-repos/ --remote-name github
```

This is useful when you have the same repository in multiple locations (e.g., GitHub and Azure DevOps mirrors).

## Command Line Options

| Option | Description | Required |
|--------|-------------|----------|
| `--target`, `-t` | Path to .gitopolis.toml file or directory containing it | Yes |
| `--owner` | GitHub owner (user or organization) name | No (defaults to authenticated user) |
| `--protocol` | Remote protocol to use: `ssh` or `https` | No (defaults to `ssh`) |
| `--remote-name` | Name for the remote when adding to existing repos | No (defaults to `origin`) |

## Troubleshooting

### "gh: command not found"
Install GitHub CLI following the instructions in Prerequisites.

### "gh auth status" shows not logged in
Run `gh auth login` and follow the prompts to authenticate.

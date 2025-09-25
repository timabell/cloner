# GitHub Repository Cloner

This Python script automatically clones all your public and private GitHub repositories and adds them to gitopolis (CLI tool) with appropriate tags.

> **Note**: This is part of a larger repository cloning project. See the [main README](../README.md) for setup instructions.

## Features

- 🔄 Clones all public and private repositories from your GitHub account
- 🏷️ Tags repositories as "public" or "private" in gitopolis
- 📝 Comprehensive logging to file and console
- 🚀 Uses GitHub CLI (`gh`) for secure authentication
- ⚡ Skips repositories that are already cloned locally
- 🛡️ Robust error handling and recovery

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

2. **Python 3.7+**: The script requires Python 3.7 or later

3. **Gitopolis CLI**: You'll need the gitopolis binary installed:
   - Download from [gitopolis releases](https://github.com/rustworkshop/gitopolis/releases)
   - Put the binary in your PATH

## Installation

See the [main README](../README.md) for installation instructions.

## Usage

### Basic Usage

To clone all repositories from your authenticated user and add them to gitopolis:

```bash
python github_cloner.py --clone-dir ./repos
```

### With Owner (User or Organization)

To clone repositories from a specific user or organization:

```bash
python github_cloner.py --clone-dir ./repos --owner myorganization
```

### Full Example

```bash
python github_cloner.py --clone-dir ~/my-repos --owner mycompany
```

## Command Line Options

| Option | Description | Required |
|--------|-------------|----------|
| `--clone-dir` | Directory where repositories will be cloned | Yes |
| `--owner` | GitHub owner (user or organization) name | No (defaults to authenticated user) |
| `--help` | Show help message | - |

## How It Works

1. **Authentication Check**: Verifies that you're logged in to GitHub via `gh auth status`
2. **Repository Discovery**: Uses `gh repo list` to find all public and private repositories
3. **Cloning**: Clones each repository using `gh repo clone` for secure authentication
4. **Gitopolis Integration**: Adds each repository to gitopolis with appropriate tags:
   - Public repositories get tagged as "public"
   - Private repositories get tagged as "private"

## Logging

The script creates detailed logs in two places:
- **Console output**: Real-time progress and status updates
- **Log file**: `github_cloner.log` with detailed information for debugging

## Gitopolis CLI Integration

The script integrates with gitopolis by:

1. **Adding repositories**: Uses `gitopolis add <repo-name>` to add each cloned repository
2. **Tagging repositories**: Uses `gitopolis tag <tag> <repo-name>` to tag repositories as "public" or "private"
3. **State management**: Creates/updates `.gitopolis.toml` file in the clone directory

## Error Handling

The script includes comprehensive error handling:
- **Network issues**: Retries and graceful degradation
- **Authentication problems**: Clear error messages with suggestions
- **File system errors**: Proper permissions checking
- **API failures**: Detailed logging of response codes and messages

## Troubleshooting

### "gh: command not found"
Install GitHub CLI following the instructions in Prerequisites.

### "gh auth status" shows not logged in
Run `gh auth login` and follow the prompts to authenticate.

### Permission denied errors
Ensure you have write permissions to the clone directory.

### Gitopolis CLI errors
- Ensure `gitopolis` binary is installed and in your PATH
- Check that you have write permissions in the clone directory
- Check the log file for detailed error messages

## Security Notes

- The script uses GitHub CLI for authentication, which securely manages tokens
- No API keys or tokens are stored in the script
- SSH keys are used for cloning when available
- All API communications use HTTPS

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.

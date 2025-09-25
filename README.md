# Repository Cloner & Gitopolis Integration

This project provides scripts to clone repositories from various source control systems and add them to [gitopolis](https://github.com/rustworkshop/gitopolis) with appropriate tags.

## Supported Systems

- **GitHub** (`github/`) - Clone public and private GitHub repositories
- **Azure DevOps** (`azure-devops/`) - Clone repositories from Azure DevOps organizations/projects

## Prerequisites

1. **Python 3.7+**: All scripts require Python 3.7 or later
2. **Gitopolis CLI**: You'll need the gitopolis binary installed:
   - Download from [gitopolis releases](https://github.com/rustworkshop/gitopolis/releases)
   - Put the binary in your PATH

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   ./dev-setup.sh
   ```

## Development

To format code and run linting across all variants:
```bash
./lint.sh
```

## Usage

See the README in each subdirectory for specific usage instructions:

- [GitHub Cloner](github/README.md)
- [Azure DevOps Cloner](azure-devops/README.md)

# Repository Cloner & Gitopolis Integration

[github.com/timabell/cloner](https://github.com/timabell/cloner)

This project provides scripts to clone repositories from various source control systems and add them to [gitopolis](https://github.com/rustworkshop/gitopolis) with appropriate tags.

## Supported Systems

- **GitHub** (`github/`) - Clone public and private GitHub repositories
- **Azure DevOps** (`azure-devops/`) - Coming soon

## Prerequisites

1. asdf-vm with python plugin - [github.com/asdf-community/asdf-python: Python plugin for the asdf version manager](https://github.com/asdf-community/asdf-python) 
2. **Gitopolis CLI**: You'll need the gitopolis binary installed:
   - Download from [gitopolis releases](https://github.com/rustworkshop/gitopolis/releases)
   - Put the binary in your PATH

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   ./dev-setup.sh
   ```

## Usage

See the README in each subdirectory for specific usage instructions:

- [GitHub Cloner](github/README.md)
- [Azure DevOps Cloner](azure-devops/README.md)

## Development

To format code and run linting across all variants:
```bash
./lint.sh
```

## License

[A-GPL v3](LICENSE)
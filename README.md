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

Run the cloner script for the system you want to clone repositories from:

- [GitHub Cloner](github/README.md)
- [Azure DevOps Cloner](azure-devops/README.md)

This will add repositories and tags to the `.gitopolis.toml`. It will create the folder & config file if they don't exist, and if they do it will extend the config with any additional tags and repositories.

Then run `gitopolis clone` to clone all repositories.

Or run `gitopolis clone --tag <tag>` to clone all repositories with the specified tag.

This will clone any repositories you don't already have cloned.

Once you've done this, you can pass the `.gitopolis.toml` around amongst your colleagues to collaborate on building tagged list of repositories.

## Development

To format code and run linting across all variants:
```bash
./lint.sh
```

## License

[A-GPL v3](LICENSE)
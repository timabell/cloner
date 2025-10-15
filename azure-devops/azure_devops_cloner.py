#!/usr/bin/env python3
"""
Azure DevOps Repository Cloner and Gitopolis Integration Script

This script clones all repositories from Azure DevOps for the authenticated user
and adds them to gitopolis with appropriate tags using the gitopolis CLI tool.
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Import shared gitopolis utilities
sys.path.append(str(Path(__file__).parent.parent))
from gitopolis_utils import add_repositories_to_gitopolis_config


class AzureDevOpsCloner:
    """Main class for discovering Azure DevOps repositories and adding them to gitopolis configuration."""

    def __init__(
        self, target: str, protocol: str = "https", remote_name: str = "devops"
    ):
        """
        Initialize the Azure DevOps Cloner.

        Args:
            target: Path to .gitopolis.toml file or directory containing it
            protocol: Remote protocol to use ('ssh' or 'https'), defaults to 'https'
            remote_name: Name for the remote when adding to existing repos, defaults to 'devops'
        """
        target_path = Path(target)

        # If target is a directory, append .gitopolis.toml
        if target_path.is_dir() or (
            not target_path.exists() and not target_path.suffix
        ):
            self.config_path = target_path / ".gitopolis.toml"
        else:
            self.config_path = target_path

        self.setup_logging()

        # Create parent directory if it doesn't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.protocol = protocol.lower()
        self.remote_name = remote_name

    def setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("azdo_cloner.log"),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def run_az_command(self, args: List[str]) -> Dict:
        """
        Run an az CLI command and return JSON output.

        Args:
            args: List of command arguments

        Returns:
            Parsed JSON response
        """
        try:
            cmd = ["az"] + args
            self.logger.info(f"Running command: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if result.stdout.strip():
                return json.loads(result.stdout)
            return {}

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {e}")
            self.logger.error(f"stderr: {e.stderr}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON output: {e}")
            self.logger.error(f"stdout: {result.stdout}")
            raise

    def get_repositories(
        self, organization: str, project: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all repositories from Azure DevOps for the specified organization/project.
        Uses az devops invoke to get all repos without pagination limits.

        Args:
            organization: Azure DevOps organization name
            project: Optional project name (if None, gets repos from all projects)

        Returns:
            List of repository dictionaries
        """
        self.logger.info(f"Fetching repositories from organization '{organization}'...")

        try:
            org_url = f"https://dev.azure.com/{organization}"

            # Use az devops invoke to get all repos (no 100 limit like az repos list)
            cmd_args = [
                "devops",
                "invoke",
                "--area",
                "git",
                "--resource",
                "repositories",
                "--org",
                org_url,
                "--api-version",
                "7.0",
                "--output",
                "json",
            ]

            result = self.run_az_command(cmd_args)

            # Azure DevOps API returns {"value": [...], "count": N}
            if isinstance(result, dict) and "value" in result:
                all_repos = result["value"]

                # Filter by project if specified
                if project:
                    self.logger.info(f"Filtering to project '{project}'")
                    all_repos = [
                        repo
                        for repo in all_repos
                        if repo.get("project", {}).get("name") == project
                    ]

                self.logger.info(f"Found {len(all_repos)} repositories")
                return all_repos
            else:
                self.logger.warning("Unexpected response format from az devops invoke")
                return []

        except Exception as e:
            self.logger.error(f"Failed to fetch repositories: {e}")
            return []

    def prepare_repo_for_gitopolis(self, repo: Dict) -> Dict:
        """
        Prepare repository data for gitopolis configuration.

        Args:
            repo: Repository dictionary from Azure DevOps API

        Returns:
            Dictionary with repo info for batch processing
        """
        repo_name = repo["name"]

        # Azure DevOps provides both HTTPS and SSH URLs
        https_url = repo.get("remoteUrl") or repo.get("webUrl")
        ssh_url = repo.get("sshUrl")

        # Use the appropriate URL based on protocol preference
        if self.protocol == "ssh" and ssh_url:
            repo_url = ssh_url
        else:
            repo_url = https_url

        # Extract and sanitize project name for tagging
        tags = ["azure-devops"]
        project_name = repo.get("project", {}).get("name")
        if project_name:
            # Replace spaces with hyphens and convert to lowercase
            sanitized_project = project_name.replace(" ", "-")
            tags.append(sanitized_project)

        return {
            "name": repo_name,
            "url": repo_url,
            "tags": tags,
        }

    def process_repositories(self, organization: str, project: Optional[str] = None):
        """Main method to process all repositories."""
        self.logger.info(
            "Starting Azure DevOps repository discovery and gitopolis integration..."
        )

        # Get all repositories
        repositories = self.get_repositories(organization, project)

        if not repositories:
            self.logger.warning("No repositories found")
            return

        # Prepare all repositories for batch processing
        self.logger.info("Preparing repositories for gitopolis configuration...")
        repo_configs = []
        for repo in repositories:
            self.logger.info(f"Processing {repo['name']}...")
            repo_config = self.prepare_repo_for_gitopolis(repo)
            repo_configs.append(repo_config)

        # Add all repositories to gitopolis config in one operation
        add_repositories_to_gitopolis_config(
            repo_configs, self.config_path, self.logger, self.remote_name
        )

        self.logger.info(f"Processing complete!")
        self.logger.info(
            f"Successfully added to gitopolis: {len(repositories)} repositories"
        )
        self.logger.info(
            f"Use 'gitopolis clone' to clone all repositories, or 'gitopolis clone --tag <tag>' for specific subsets."
        )


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Discover Azure DevOps repositories and add to gitopolis configuration"
    )
    parser.add_argument(
        "--target",
        "-t",
        required=True,
        help="Path to .gitopolis.toml file or directory containing it (required)",
    )
    parser.add_argument(
        "--organization",
        required=True,
        help="Azure DevOps organization name (required)",
    )
    parser.add_argument(
        "--project",
        help="Azure DevOps project name (optional, if not specified will discover from all projects)",
    )
    parser.add_argument(
        "--protocol",
        choices=["ssh", "https"],
        default="https",
        help="Remote protocol to use (default: https)",
    )
    parser.add_argument(
        "--remote-name",
        default="devops",
        help="Name for the remote when adding to existing repos (default: devops)",
    )

    args = parser.parse_args()

    try:
        cloner = AzureDevOpsCloner(
            target=args.target, protocol=args.protocol, remote_name=args.remote_name
        )
        cloner.process_repositories(args.organization, args.project)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

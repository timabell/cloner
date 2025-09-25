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
from gitopolis_utils import add_repository_to_gitopolis_config


class AzureDevOpsCloner:
    """Main class for discovering Azure DevOps repositories and adding them to gitopolis configuration."""

    def __init__(self, target: str):
        """
        Initialize the Azure DevOps Cloner.

        Args:
            target: Path to .gitopolis.toml file or directory containing it
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

        Args:
            organization: Azure DevOps organization name
            project: Optional project name (if None, gets repos from all projects)

        Returns:
            List of repository dictionaries
        """
        self.logger.info(f"Fetching repositories from organization '{organization}'...")

        try:
            cmd_args = [
                "repos",
                "list",
                "--organization",
                f"https://dev.azure.com/{organization}",
                "--output",
                "json",
            ]

            if project:
                cmd_args.extend(["--project", project])
                self.logger.info(f"Limiting to project '{project}'")

            repos = self.run_az_command(cmd_args)

            if isinstance(repos, list):
                self.logger.info(f"Found {len(repos)} repositories")
                return repos
            else:
                self.logger.warning("Unexpected response format from az repos list")
                return []

        except Exception as e:
            self.logger.error(f"Failed to fetch repositories: {e}")
            return []

    def add_to_gitopolis(self, repo: Dict) -> bool:
        """
        Add repository to gitopolis configuration and tag it appropriately.

        Args:
            repo: Repository dictionary from Azure DevOps API

        Returns:
            True if successful, False otherwise
        """
        repo_name = repo["name"]
        repo_url = repo.get("remoteUrl") or repo.get("webUrl")

        # Azure DevOps repos are always private
        visibility_tag = "private"

        return add_repository_to_gitopolis_config(
            repo_name=repo_name,
            repo_url=repo_url,
            config_path=self.config_path,
            visibility_tag=visibility_tag,
            source_tag="azuredevops",
            logger=self.logger,
        )

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

        gitopolis_count = 0

        for repo in repositories:
            self.logger.info(f"Processing {repo['name']}...")

            # Add to gitopolis config (will raise on error)
            self.add_to_gitopolis(repo)
            gitopolis_count += 1

        self.logger.info(f"Processing complete!")
        self.logger.info(
            f"Successfully added to gitopolis: {gitopolis_count}/{len(repositories)} repositories"
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

    args = parser.parse_args()

    try:
        cloner = AzureDevOpsCloner(target=args.target)
        cloner.process_repositories(args.organization, args.project)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

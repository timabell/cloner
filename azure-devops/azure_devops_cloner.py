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
from gitopolis_utils import add_repository_to_gitopolis


class AzureDevOpsCloner:
    """Main class for cloning Azure DevOps repositories and integrating with gitopolis CLI."""

    def __init__(self, clone_dir: str = "./repos"):
        """
        Initialize the Azure DevOps Cloner.

        Args:
            clone_dir: Directory where repositories will be cloned
        """
        self.clone_dir = Path(clone_dir)
        self.setup_logging()

        # Create clone directory if it doesn't exist
        self.clone_dir.mkdir(parents=True, exist_ok=True)

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

    def clone_repository(self, repo: Dict) -> Optional[Path]:
        """
        Clone a single repository.

        Args:
            repo: Repository dictionary from Azure DevOps API

        Returns:
            Path to cloned repository or None if failed
        """
        repo_name = repo["name"]
        repo_path = self.clone_dir / repo_name

        # Skip if already exists
        if repo_path.exists():
            self.logger.info(f"Repository {repo_name} already exists, skipping clone")
            return repo_path

        try:
            self.logger.info(f"Cloning {repo_name}...")

            # Use git clone with the remote URL
            clone_url = repo.get("remoteUrl") or repo.get("webUrl")
            if not clone_url:
                self.logger.error(f"No clone URL found for {repo_name}")
                return None

            subprocess.run(
                ["git", "clone", clone_url, str(repo_path)],
                check=True,
                cwd=self.clone_dir,
            )

            self.logger.info(f"Successfully cloned {repo_name}")
            return repo_path

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to clone {repo_name}: {e}")
            return None

    def add_to_gitopolis(self, repo: Dict, repo_path: Path) -> bool:
        """
        Add repository to gitopolis CLI and tag it appropriately.

        Args:
            repo: Repository dictionary from Azure DevOps API
            repo_path: Local path to cloned repository

        Returns:
            True if successful, False otherwise
        """
        repo_name = repo["name"]

        # Azure DevOps repos are always private
        visibility_tag = "private"

        return add_repository_to_gitopolis(
            repo_name=repo_name,
            clone_dir=self.clone_dir,
            visibility_tag=visibility_tag,
            source_tag="azuredevops",
            logger=self.logger,
        )

    def process_repositories(self, organization: str, project: Optional[str] = None):
        """Main method to process all repositories."""
        self.logger.info(
            "Starting Azure DevOps repository cloning and gitopolis integration..."
        )

        # Get all repositories
        repositories = self.get_repositories(organization, project)

        if not repositories:
            self.logger.warning("No repositories found")
            return

        success_count = 0
        gitopolis_count = 0

        for repo in repositories:
            self.logger.info(f"Processing {repo['name']}...")

            # Clone repository
            repo_path = self.clone_repository(repo)

            if repo_path:
                success_count += 1

                # Add to gitopolis
                if self.add_to_gitopolis(repo, repo_path):
                    gitopolis_count += 1

        self.logger.info(f"Processing complete!")
        self.logger.info(
            f"Successfully cloned: {success_count}/{len(repositories)} repositories"
        )
        self.logger.info(
            f"Successfully added to gitopolis: {gitopolis_count}/{len(repositories)} repositories"
        )


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Clone Azure DevOps repositories and add to gitopolis"
    )
    parser.add_argument(
        "--clone-dir",
        required=True,
        help="Directory to clone repositories into (required)",
    )
    parser.add_argument(
        "--organization",
        required=True,
        help="Azure DevOps organization name (required)",
    )
    parser.add_argument(
        "--project",
        help="Azure DevOps project name (optional, if not specified will clone from all projects)",
    )

    args = parser.parse_args()

    try:
        cloner = AzureDevOpsCloner(clone_dir=args.clone_dir)
        cloner.process_repositories(args.organization, args.project)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

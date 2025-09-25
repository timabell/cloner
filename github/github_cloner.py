#!/usr/bin/env python3
"""
GitHub Repository Cloner and Gitopolis Integration Script

This script clones all public and private GitHub repositories for the authenticated user
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


class GitHubCloner:
    """Main class for discovering GitHub repositories and adding them to gitopolis configuration."""

    def __init__(self, target: str):
        """
        Initialize the GitHub Cloner.

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
                logging.FileHandler("github_cloner.log"),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def run_gh_command(self, args: List[str]) -> Dict:
        """
        Run a gh CLI command and return JSON output.

        Args:
            args: List of command arguments

        Returns:
            Parsed JSON response
        """
        try:
            cmd = ["gh"] + args
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

    def get_repositories(self, owner: Optional[str] = None) -> List[Dict]:
        """
        Get all repositories (public and private) for the authenticated user or specified owner.

        Args:
            owner: Optional owner (user or organization) name to limit repositories to

        Returns:
            List of repository dictionaries
        """
        if owner:
            self.logger.info(f"Fetching repositories from owner '{owner}'...")
        else:
            self.logger.info("Fetching all repositories for authenticated user...")

        all_repos = []

        # Build base command args
        base_args = [
            "repo",
            "list",
            "--json",
            "name,nameWithOwner,isPrivate,sshUrl,description,primaryLanguage,visibility",
            "--limit",
            "1000",
        ]

        # Add owner if specified
        if owner:
            base_args.append(owner)

        # Get public repositories
        try:
            public_args = base_args + ["--visibility", "public"]
            public_repos = self.run_gh_command(public_args)
            if isinstance(public_repos, list):
                all_repos.extend(public_repos)
                self.logger.info(f"Found {len(public_repos)} public repositories")
        except Exception as e:
            self.logger.error(f"Failed to fetch public repositories: {e}")

        # Get private repositories
        try:
            private_args = base_args + ["--visibility", "private"]
            private_repos = self.run_gh_command(private_args)
            if isinstance(private_repos, list):
                all_repos.extend(private_repos)
                self.logger.info(f"Found {len(private_repos)} private repositories")
        except Exception as e:
            self.logger.error(f"Failed to fetch private repositories: {e}")

        self.logger.info(f"Total repositories found: {len(all_repos)}")
        return all_repos

    def add_to_gitopolis(self, repo: Dict) -> bool:
        """
        Add repository to gitopolis configuration and tag it appropriately.

        Args:
            repo: Repository dictionary from GitHub API

        Returns:
            True if successful, False otherwise
        """
        repo_name = repo["name"]
        repo_url = repo["sshUrl"]

        # GitHub visibility: use the visibility field directly
        visibility = repo.get("visibility", "").upper()
        if visibility == "INTERNAL":
            visibility_tag = "internal"
        elif visibility == "PRIVATE" or repo.get("isPrivate", False):
            visibility_tag = "private"
        else:
            visibility_tag = "public"

        return add_repository_to_gitopolis_config(
            repo_name=repo_name,
            repo_url=repo_url,
            config_path=self.config_path,
            visibility_tag=visibility_tag,
            source_tag="github",
            logger=self.logger,
        )

    def process_repositories(self, owner: Optional[str] = None):
        """Main method to process all repositories."""
        self.logger.info(
            "Starting GitHub repository discovery and gitopolis integration..."
        )

        # Get all repositories
        repositories = self.get_repositories(owner)

        if not repositories:
            self.logger.warning("No repositories found")
            return

        gitopolis_count = 0

        for repo in repositories:
            self.logger.info(f"Processing {repo['nameWithOwner']}...")

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
        description="Discover GitHub repositories and add to gitopolis configuration"
    )
    parser.add_argument(
        "--target",
        "-t",
        required=True,
        help="Path to .gitopolis.toml file or directory containing it (required)",
    )
    parser.add_argument(
        "--owner",
        help="GitHub owner (user or organization) name (optional, if not specified will discover from authenticated user)",
    )
    args = parser.parse_args()

    try:
        cloner = GitHubCloner(target=args.target)
        cloner.process_repositories(args.owner)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

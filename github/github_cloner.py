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
from gitopolis_utils import add_repositories_to_gitopolis_config


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

    def get_all_repositories_via_api(self, owner: Optional[str] = None) -> List[Dict]:
        """
        Get all repositories using GitHub API with automatic pagination.

        Args:
            owner: Optional owner (user or organization) name to limit repositories to

        Returns:
            List of repository dictionaries
        """
        try:
            # Determine API endpoint
            if owner:
                # Use search API for organizations we don't have admin access to
                api_path = f"/search/repositories"
                search_query = f"org:{owner}"
            else:
                api_path = "/user/repos"

            self.logger.info(f"Fetching all repositories via GitHub API...")

            # Use gh api with --paginate to get ALL repositories automatically
            if owner:
                # Search API for organization repositories
                cmd = [
                    "gh",
                    "api",
                    f"/search/repositories?q=org:{owner}&per_page=100",
                    "--paginate",
                    "--jq",
                    ".items[]",
                ]
            else:
                # User repos API
                cmd = [
                    "gh",
                    "api",
                    "/user/repos?per_page=100&sort=updated",
                    "--paginate",
                    "--jq",
                    ".[]",
                ]

            self.logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if not result.stdout.strip():
                return []

            # Parse each line as JSON (jq outputs one repo per line)
            repos = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    try:
                        repo = json.loads(line)
                        # Convert to format expected by our code
                        formatted_repo = {
                            "name": repo["name"],
                            "nameWithOwner": repo["full_name"],
                            "isPrivate": repo["private"],
                            "sshUrl": repo["ssh_url"],
                            "visibility": repo.get(
                                "visibility", "private" if repo["private"] else "public"
                            ).upper(),
                        }
                        repos.append(formatted_repo)
                    except json.JSONDecodeError:
                        continue

            self.logger.info(f"Found {len(repos)} total repositories")
            return repos

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to fetch repositories via API: {e}")
            self.logger.error(f"stderr: {e.stderr}")
            return []
        except Exception as e:
            self.logger.error(f"Error fetching repositories: {e}")
            return []

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

        # Get all repositories using GitHub API with proper pagination
        return self.get_all_repositories_via_api(owner)

    def prepare_repo_for_gitopolis(self, repo: Dict) -> Dict:
        """
        Prepare repository data for gitopolis configuration.

        Args:
            repo: Repository dictionary from GitHub API

        Returns:
            Dictionary with repo info for batch processing
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

        return {
            "name": repo_name,
            "url": repo_url,
            "visibility_tag": visibility_tag,
            "source_tag": "github",
        }

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

        # Prepare all repositories for batch processing
        self.logger.info("Preparing repositories for gitopolis configuration...")
        repo_configs = []
        for repo in repositories:
            self.logger.info(f"Processing {repo['nameWithOwner']}...")
            repo_config = self.prepare_repo_for_gitopolis(repo)
            repo_configs.append(repo_config)

        # Add all repositories to gitopolis config in one operation
        add_repositories_to_gitopolis_config(
            repo_configs, self.config_path, self.logger
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

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


class GitHubCloner:
    """Main class for cloning GitHub repositories and integrating with gitopolis CLI."""

    def __init__(self, clone_dir: str = "./repos"):
        """
        Initialize the GitHub Cloner.

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

    def clone_repository(self, repo: Dict) -> Optional[Path]:
        """
        Clone a single repository.

        Args:
            repo: Repository dictionary from GitHub API

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
            self.logger.info(f"Cloning {repo['nameWithOwner']}...")

            # Use gh repo clone for better authentication handling
            subprocess.run(
                ["gh", "repo", "clone", repo["nameWithOwner"], str(repo_path)],
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
            repo: Repository dictionary from GitHub API
            repo_path: Local path to cloned repository

        Returns:
            True if successful, False otherwise
        """
        try:
            repo_name = repo["name"]
            tag = "private" if repo["isPrivate"] else "public"

            self.logger.info(f"Adding {repo_name} to gitopolis with tag '{tag}'...")

            # Add repository to gitopolis
            add_result = subprocess.run(
                ["gitopolis", "add", repo_name],
                cwd=self.clone_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            if add_result.returncode != 0:
                self.logger.warning(
                    f"Failed to add {repo_name} to gitopolis: {add_result.stderr}"
                )
                return False

            # Tag the repository with visibility
            tag_result = subprocess.run(
                ["gitopolis", "tag", tag, repo_name],
                cwd=self.clone_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            if tag_result.returncode != 0:
                self.logger.warning(
                    f"Failed to tag {repo_name} with '{tag}': {tag_result.stderr}"
                )
                return False

            # Tag the repository with source platform
            github_tag_result = subprocess.run(
                ["gitopolis", "tag", "github", repo_name],
                cwd=self.clone_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            if github_tag_result.returncode != 0:
                self.logger.warning(
                    f"Failed to tag {repo_name} with 'github': {github_tag_result.stderr}"
                )
                return False

            self.logger.info(
                f"Successfully added {repo_name} to gitopolis with tags '{tag}' and 'github'"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error adding {repo_name} to gitopolis: {e}")
            return False

    def process_repositories(self, owner: Optional[str] = None):
        """Main method to process all repositories."""
        self.logger.info(
            "Starting GitHub repository cloning and gitopolis integration..."
        )

        # Get all repositories
        repositories = self.get_repositories(owner)

        if not repositories:
            self.logger.warning("No repositories found")
            return

        success_count = 0
        gitopolis_count = 0

        for repo in repositories:
            self.logger.info(f"Processing {repo['nameWithOwner']}...")

            # Clone repository
            repo_path = self.clone_repository(repo)

            if repo_path:
                success_count += 1

                # Add to Gitopolis
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
        description="Clone GitHub repositories and add to gitopolis"
    )
    parser.add_argument(
        "--clone-dir",
        required=True,
        help="Directory to clone repositories into (required)",
    )
    parser.add_argument(
        "--owner",
        help="GitHub owner (user or organization) name (optional, if not specified will clone from authenticated user)",
    )
    args = parser.parse_args()

    try:
        cloner = GitHubCloner(clone_dir=args.clone_dir)
        cloner.process_repositories(args.owner)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

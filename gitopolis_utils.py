"""
Shared utilities for gitopolis integration.

This module provides common functionality for adding repositories to gitopolis
and tagging them appropriately.
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List


def add_repository_to_gitopolis(
    repo_name: str,
    clone_dir: Path,
    visibility_tag: str,
    source_tag: str,
    logger: logging.Logger,
) -> bool:
    """
    Add a repository to gitopolis and tag it with visibility and source tags.

    Args:
        repo_name: Name of the repository
        clone_dir: Directory where repositories are cloned
        visibility_tag: Tag for repository visibility ("public", "private", etc.)
        source_tag: Tag for source platform ("github", "azuredevops", etc.)
        logger: Logger instance for output

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Adding {repo_name} to gitopolis with tags '{visibility_tag}' and '{source_tag}'...")

        # Add repository to gitopolis
        add_result = subprocess.run(
            ["gitopolis", "add", repo_name],
            cwd=clone_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if add_result.returncode != 0:
            logger.warning(
                f"Failed to add {repo_name} to gitopolis: {add_result.stderr}"
            )
            return False

        # Tag the repository with visibility
        visibility_tag_result = subprocess.run(
            ["gitopolis", "tag", visibility_tag, repo_name],
            cwd=clone_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if visibility_tag_result.returncode != 0:
            logger.warning(
                f"Failed to tag {repo_name} with '{visibility_tag}': {visibility_tag_result.stderr}"
            )
            return False

        # Tag the repository with source platform
        source_tag_result = subprocess.run(
            ["gitopolis", "tag", source_tag, repo_name],
            cwd=clone_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if source_tag_result.returncode != 0:
            logger.warning(
                f"Failed to tag {repo_name} with '{source_tag}': {source_tag_result.stderr}"
            )
            return False

        logger.info(
            f"Successfully added {repo_name} to gitopolis with tags '{visibility_tag}' and '{source_tag}'"
        )
        return True

    except Exception as e:
        logger.error(f"Error adding {repo_name} to gitopolis: {e}")
        return False



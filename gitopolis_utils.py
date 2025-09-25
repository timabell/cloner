"""
Shared utilities for gitopolis integration.

This module provides common functionality for managing .gitopolis.toml files
and adding repositories with appropriate tags.
"""

import logging
import toml
from pathlib import Path
from typing import Dict, List, Set


def load_gitopolis_config(config_path: Path) -> Dict:
    """
    Load existing .gitopolis.toml configuration or create a new one.

    Args:
        config_path: Path to .gitopolis.toml file

    Returns:
        Dictionary containing gitopolis configuration
    """
    if config_path.exists():
        try:
            return toml.load(config_path)
        except Exception as e:
            # If file is corrupted, die rather than lose data
            raise RuntimeError(f"Corrupted gitopolis config at {config_path}: {e}")
    
    # Return default structure matching gitopolis format
    return {
        "repos": []
    }


def save_gitopolis_config(config_path: Path, config: Dict) -> bool:
    """
    Save gitopolis configuration to .gitopolis.toml file.

    Args:
        config_path: Path to .gitopolis.toml file
        config: Configuration dictionary to save

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(config_path, 'w') as f:
            toml.dump(config, f)
        return True
    except Exception:
        return False


def add_repository_to_gitopolis_config(
    repo_name: str,
    repo_url: str,
    config_path: Path,
    visibility_tag: str,
    source_tag: str,
    logger: logging.Logger,
) -> bool:
    """
    Add a repository to gitopolis configuration with visibility and source tags.

    Args:
        repo_name: Name of the repository
        repo_url: Git URL for the repository
        config_path: Path to .gitopolis.toml file
        visibility_tag: Tag for repository visibility ("public", "private", etc.)
        source_tag: Tag for source platform ("github", "azuredevops", etc.)
        logger: Logger instance for output

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Adding {repo_name} to gitopolis config with tags '{visibility_tag}' and '{source_tag}'...")

        # Load existing config
        config = load_gitopolis_config(config_path)

        # Add repository if not exists (repos is a list of dicts)
        repo_exists = any(repo.get("path") == repo_name for repo in config["repos"])
        if not repo_exists:
            config["repos"].append({
                "path": repo_name,
                "tags": [visibility_tag, source_tag],
                "remotes": {
                    "origin": {
                        "name": "origin",
                        "url": repo_url
                    }
                }
            })
        else:
            # Update existing repo's tags
            for repo in config["repos"]:
                if repo.get("path") == repo_name:
                    if "tags" not in repo:
                        repo["tags"] = []
                    if visibility_tag not in repo["tags"]:
                        repo["tags"].append(visibility_tag)
                    if source_tag not in repo["tags"]:
                        repo["tags"].append(source_tag)
                    # Update remote URL if needed
                    if "remotes" not in repo:
                        repo["remotes"] = {}
                    if "origin" not in repo["remotes"]:
                        repo["remotes"]["origin"] = {}
                    repo["remotes"]["origin"]["name"] = "origin"
                    repo["remotes"]["origin"]["url"] = repo_url
                    break

        # No global tags needed - gitopolis only uses per-repo tags

        # Save config
        if save_gitopolis_config(config_path, config):
            logger.info(f"Successfully added {repo_name} to gitopolis config")
            return True
        else:
            logger.error(f"Failed to save gitopolis config for {repo_name}")
            raise RuntimeError(f"Failed to save gitopolis config for {repo_name}")

    except Exception as e:
        logger.error(f"Error adding {repo_name} to gitopolis config: {e}")
        raise RuntimeError(f"Failed to add {repo_name} to gitopolis config: {e}")



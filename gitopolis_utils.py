"""
Shared utilities for gitopolis integration.

This module provides common functionality for managing .gitopolis.toml files
and adding repositories with appropriate tags.
"""

import logging
import toml
from pathlib import Path
from typing import Dict, List


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


def add_repositories_to_gitopolis_config(
    repositories: List[Dict],
    config_path: Path,
    logger: logging.Logger,
) -> bool:
    """
    Add multiple repositories to gitopolis configuration in one operation.

    Args:
        repositories: List of repository dicts with keys: name, url, visibility_tag, source_tag
        config_path: Path to .gitopolis.toml file
        logger: Logger instance for output

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Adding {len(repositories)} repositories to gitopolis config...")

        # Load existing config
        config = load_gitopolis_config(config_path)

        # Process all repositories
        for repo_info in repositories:
            repo_name = repo_info["name"]
            repo_url = repo_info["url"]
            visibility_tag = repo_info["visibility_tag"]
            source_tag = repo_info["source_tag"]

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

        # Save config once at the end
        if save_gitopolis_config(config_path, config):
            logger.info(f"Successfully added {len(repositories)} repositories to gitopolis config")
            return True
        else:
            logger.error(f"Failed to save gitopolis config")
            raise RuntimeError(f"Failed to save gitopolis config")

    except Exception as e:
        logger.error(f"Error adding repositories to gitopolis config: {e}")
        raise RuntimeError(f"Failed to add repositories to gitopolis config: {e}")


def add_repository_to_gitopolis_config(
    repo_name: str,
    repo_url: str,
    config_path: Path,
    visibility_tag: str,
    source_tag: str,
    logger: logging.Logger,
) -> bool:
    """
    Add a single repository to gitopolis configuration (legacy function for compatibility).
    For better performance, use add_repositories_to_gitopolis_config for multiple repos.

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
    repositories = [{
        "name": repo_name,
        "url": repo_url,
        "visibility_tag": visibility_tag,
        "source_tag": source_tag
    }]
    return add_repositories_to_gitopolis_config(repositories, config_path, logger)



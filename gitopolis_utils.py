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


def _find_existing_repo(config: Dict, repo_name: str) -> Dict | None:
    """
    Find an existing repository in the config by name.

    Args:
        config: Gitopolis configuration dictionary
        repo_name: Name of the repository to find

    Returns:
        Repository dictionary if found, None otherwise
    """
    for repo in config["repos"]:
        if repo.get("path") == repo_name:
            return repo
    return None


def _create_new_repo_entry(repo_name: str, repo_url: str, repo_tags: List[str]) -> Dict:
    """
    Create a new repository entry for gitopolis config.

    Args:
        repo_name: Name of the repository
        repo_url: Git URL for the repository
        repo_tags: List of tags for the repository

    Returns:
        Dictionary representing a new repository entry
    """
    return {
        "path": repo_name,
        "tags": repo_tags,
        "remotes": {
            "origin": {
                "name": "origin",
                "url": repo_url
            }
        }
    }


def _merge_tags(existing_repo: Dict, new_tags: List[str]) -> None:
    """
    Merge new tags into an existing repository entry.

    Args:
        existing_repo: Existing repository dictionary
        new_tags: List of new tags to add
    """
    if "tags" not in existing_repo:
        existing_repo["tags"] = []
    
    for tag in new_tags:
        if tag not in existing_repo["tags"]:
            existing_repo["tags"].append(tag)


def _url_exists_in_remotes(existing_repo: Dict, url: str) -> bool:
    """
    Check if a URL already exists in any remote of the repository.

    Args:
        existing_repo: Existing repository dictionary
        url: URL to check for

    Returns:
        True if URL exists in any remote, False otherwise
    """
    if "remotes" not in existing_repo:
        return False
    
    return any(
        remote.get("url") == url
        for remote in existing_repo["remotes"].values()
    )


def _find_unique_remote_name(existing_repo: Dict, base_name: str) -> str:
    """
    Find a unique remote name by appending numbers if needed.

    Args:
        existing_repo: Existing repository dictionary
        base_name: Base name for the remote

    Returns:
        Unique remote name
    """
    if "remotes" not in existing_repo:
        return base_name
    
    remote_name = base_name
    counter = 1
    while remote_name in existing_repo["remotes"]:
        remote_name = f"{base_name}{counter}"
        counter += 1
    
    return remote_name


def _add_remote_to_repo(existing_repo: Dict, remote_name: str, url: str) -> None:
    """
    Add a new remote to an existing repository.

    Args:
        existing_repo: Existing repository dictionary
        remote_name: Name for the new remote
        url: URL for the new remote
    """
    if "remotes" not in existing_repo:
        existing_repo["remotes"] = {}
    
    existing_repo["remotes"][remote_name] = {
        "name": remote_name,
        "url": url
    }


def _process_new_repository(
    config: Dict,
    repo_name: str,
    repo_url: str,
    repo_tags: List[str],
    logger: logging.Logger,
) -> None:
    """
    Add a new repository to the config.

    Args:
        config: Gitopolis configuration dictionary
        repo_name: Name of the repository
        repo_url: Git URL for the repository
        repo_tags: List of tags for the repository
        logger: Logger instance for output
    """
    new_repo = _create_new_repo_entry(repo_name, repo_url, repo_tags)
    config["repos"].append(new_repo)
    logger.info(f"Added new repository: {repo_name}")


def _process_existing_repository(
    existing_repo: Dict,
    repo_name: str,
    repo_url: str,
    repo_tags: List[str],
    remote_name: str,
    logger: logging.Logger,
) -> None:
    """
    Update an existing repository with new tags and/or remotes.

    Args:
        existing_repo: Existing repository dictionary
        repo_name: Name of the repository
        repo_url: Git URL for the repository
        repo_tags: List of tags to merge
        remote_name: Base name for new remote
        logger: Logger instance for output
    """
    # Merge tags
    _merge_tags(existing_repo, repo_tags)

    # Check if URL already exists
    if _url_exists_in_remotes(existing_repo, repo_url):
        logger.info(f"Repository {repo_name} already has URL {repo_url}, skipping")
        return

    # Add new remote with unique name
    unique_remote_name = _find_unique_remote_name(existing_repo, remote_name)
    _add_remote_to_repo(existing_repo, unique_remote_name, repo_url)
    logger.info(f"Added remote '{unique_remote_name}' to existing repository: {repo_name}")


def add_repositories_to_gitopolis_config(
    repositories: List[Dict],
    config_path: Path,
    logger: logging.Logger,
    remote_name: str = "origin",
) -> bool:
    """
    Add multiple repositories to gitopolis configuration in one operation.

    Args:
        repositories: List of repository dicts with keys: name, url, visibility_tag, source_tag
        config_path: Path to .gitopolis.toml file
        logger: Logger instance for output
        remote_name: Name for the remote when adding to existing repos (default: "origin")

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
            repo_tags = repo_info.get("tags", [])

            existing_repo = _find_existing_repo(config, repo_name)

            if existing_repo is None:
                _process_new_repository(config, repo_name, repo_url, repo_tags, logger)
            else:
                _process_existing_repository(
                    existing_repo, repo_name, repo_url, repo_tags, remote_name, logger
                )

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



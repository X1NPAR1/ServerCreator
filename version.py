"""
Central application metadata for ServerCreator.

This module is the single source of truth for the application version,
publisher information and the GitHub repository used by the automatic
update mechanism. Keeping these values in one place guarantees that the
installer, the auto-updater and the user interface always agree.
"""

# Semantic version of the application. The leading "v" is added where a tag
# style string is required (for example when comparing against GitHub release
# tags such as "v1.75.2").
APP_VERSION = "1.76.0"

# Display name of the application.
APP_NAME = "ServerCreator"

# Publisher / author shown in the installer and the about section.
APP_PUBLISHER = "X1NPAR1"

# GitHub repository that hosts the published releases (setup files).
# The auto-updater queries the GitHub Releases API of this repository on every
# launch to determine whether a newer setup has been published.
#   GITHUB_OWNER / GITHUB_RELEASE_REPO  -> binary releases (setup .exe)
#   GITHUB_OWNER / GITHUB_SOURCE_REPO   -> public source code
GITHUB_OWNER = "X1NPAR1"
GITHUB_RELEASE_REPO = "ServerCreator-Release"
GITHUB_SOURCE_REPO = "ServerCreator"

# Convenience accessors -------------------------------------------------------


def version_tag() -> str:
    """Return the version formatted as a Git tag (e.g. ``v1.75.2``)."""
    return f"v{APP_VERSION}"


def releases_api_url() -> str:
    """Return the GitHub API endpoint for the latest published release."""
    return (
        f"https://api.github.com/repos/{GITHUB_OWNER}/"
        f"{GITHUB_RELEASE_REPO}/releases/latest"
    )

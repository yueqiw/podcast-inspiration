import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from models import Newsletter
from .markdown_generator import generate_newsletter

logger = logging.getLogger(__name__)

# Default archive directory
ARCHIVE_DIR = Path(__file__).parent.parent / "newsletters"


def archive_newsletter(
    newsletter: Newsletter,
    archive_dir: Path = ARCHIVE_DIR,
) -> Path:
    """Archive newsletter to local filesystem.

    Args:
        newsletter: The newsletter to archive.
        archive_dir: Directory to save newsletters.

    Returns:
        Path to the saved newsletter file.
    """
    # Ensure archive directory exists
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with date
    date_str = newsletter.date.strftime("%Y-%m-%d")
    filename = f"newsletter_{date_str}.md"
    filepath = archive_dir / filename

    # Generate markdown content if not already done
    if not newsletter.markdown_content:
        newsletter.markdown_content = generate_newsletter(newsletter)

    # Write to file
    filepath.write_text(newsletter.markdown_content, encoding="utf-8")
    logger.info(f"Newsletter archived to: {filepath}")

    return filepath


def get_archived_newsletters(archive_dir: Path = ARCHIVE_DIR) -> List[Path]:
    """Get list of archived newsletter files.

    Args:
        archive_dir: Directory containing newsletters.

    Returns:
        List of newsletter file paths, sorted by date (newest first).
    """
    if not archive_dir.exists():
        return []

    files = list(archive_dir.glob("newsletter_*.md"))
    return sorted(files, reverse=True)


def get_latest_newsletter(archive_dir: Path = ARCHIVE_DIR) -> Optional[Path]:
    """Get the most recent archived newsletter.

    Args:
        archive_dir: Directory containing newsletters.

    Returns:
        Path to latest newsletter, or None if no newsletters exist.
    """
    newsletters = get_archived_newsletters(archive_dir)
    return newsletters[0] if newsletters else None

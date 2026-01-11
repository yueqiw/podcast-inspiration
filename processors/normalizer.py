import html
import re
from typing import Optional, List

from models import Episode


def normalize_episodes(episodes: List[Episode]) -> List[Episode]:
    """Normalize episode data across different sources.

    Cleans up text fields, ensures consistent formatting, and
    removes duplicates within the same source.
    """
    normalized = []
    seen_ids = set()

    for episode in episodes:
        if episode.id in seen_ids:
            continue
        seen_ids.add(episode.id)

        normalized_episode = _normalize_episode(episode)
        if normalized_episode:
            normalized.append(normalized_episode)

    return normalized


def _normalize_episode(episode: Episode) -> Optional[Episode]:
    """Normalize a single episode's data."""
    try:
        # Clean title
        title = clean_text(episode.title)
        if not title or len(title) < 3:
            return None

        # Clean podcast title
        podcast_title = clean_text(episode.podcast_title)
        if not podcast_title:
            podcast_title = "Unknown Podcast"

        # Clean description
        description = clean_text(episode.description or "")
        description = truncate_text(description, max_length=500)

        # Create normalized copy
        return Episode(
            id=episode.id,
            title=title,
            podcast_title=podcast_title,
            podcast_author=clean_text(episode.podcast_author) if episode.podcast_author else None,
            description=description,
            summary=episode.summary,
            published_at=episode.published_at,
            duration_seconds=episode.duration_seconds,
            audio_url=episode.audio_url,
            episode_url=episode.episode_url,
            image_url=episode.image_url,
            source=episode.source,
            source_categories=episode.source_categories,
            matched_category=episode.matched_category,
        )
    except Exception:
        return None


def clean_text(text: Optional[str]) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""

    # Decode HTML entities
    text = html.unescape(text)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max length, breaking at word boundaries."""
    if len(text) <= max_length:
        return text

    truncated = text[:max_length]
    # Try to break at the last space
    last_space = truncated.rfind(" ")
    if last_space > max_length // 2:
        truncated = truncated[:last_space]

    return truncated.rstrip(".,!?;:") + "..."

import re
from collections import defaultdict
from typing import List, Dict

from models import Episode, Source


def deduplicate_episodes(episodes: List[Episode]) -> List[Episode]:
    """Remove duplicate episodes across different sources.

    Uses fuzzy matching on title and podcast name to identify
    the same episode from different sources. Prefers episodes
    with more complete data.
    """
    # Group by normalized podcast+episode title
    groups: Dict[str, List[Episode]] = defaultdict(list)

    for episode in episodes:
        key = _get_dedup_key(episode)
        groups[key].append(episode)

    # Pick the best episode from each group
    deduplicated = []
    for group_episodes in groups.values():
        best = _pick_best_episode(group_episodes)
        deduplicated.append(best)

    return deduplicated


def _get_dedup_key(episode: Episode) -> str:
    """Generate a normalized key for deduplication."""
    podcast = _normalize_for_matching(episode.podcast_title)
    title = _normalize_for_matching(episode.title)

    # Create a key that's resilient to minor differences
    return f"{podcast[:30]}|{title[:50]}"


def _normalize_for_matching(text: str) -> str:
    """Normalize text for fuzzy matching."""
    text = text.lower()

    # Remove common podcast prefixes/suffixes
    text = re.sub(r"^(the|a|an)\s+", "", text)
    text = re.sub(r"\s*(podcast|show|episode|ep\.?|#\d+).*$", "", text)

    # Remove special characters
    text = re.sub(r"[^\w\s]", "", text)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _pick_best_episode(episodes: List[Episode]) -> Episode:
    """Pick the best episode from a group of duplicates.

    Scoring criteria:
    - Has description: +2
    - Has published date: +2
    - Has duration: +1
    - Has episode URL: +1
    - Has audio URL: +1
    - Source priority (Podcast Index > Spotify > Apple > Listen Notes): +0-3
    """
    if len(episodes) == 1:
        return episodes[0]

    source_priority = {
        Source.PODCAST_INDEX: 3,
        Source.SPOTIFY: 2,
        Source.APPLE_PODCASTS: 1,
        Source.LISTEN_NOTES: 0,
    }

    def score(ep: Episode) -> int:
        s = 0
        if ep.description and len(ep.description) > 50:
            s += 2
        if ep.published_at:
            s += 2
        if ep.duration_seconds:
            s += 1
        if ep.episode_url:
            s += 1
        if ep.audio_url:
            s += 1
        s += source_priority.get(ep.source, 0)
        return s

    return max(episodes, key=score)

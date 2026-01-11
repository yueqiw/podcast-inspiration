import re
from collections import Counter
from typing import List, Dict

from models import Episode, Category
from config.settings import CATEGORY_KEYWORDS


def categorize_episodes(episodes: List[Episode]) -> List[Episode]:
    """Categorize episodes based on content matching.

    Assigns each episode to the most relevant category based on
    keyword matching in title, description, and source categories.
    """
    categorized = []

    for episode in episodes:
        category = _match_category(episode)
        # Create a copy with the matched category
        categorized_episode = episode.copy(update={"matched_category": category})
        categorized.append(categorized_episode)

    return categorized


def _match_category(episode: Episode) -> Category:
    """Match an episode to the best category."""
    # Combine text for matching
    text_to_match = " ".join([
        episode.title.lower(),
        (episode.description or "").lower(),
        episode.podcast_title.lower(),
        " ".join(episode.source_categories).lower(),
    ])

    # Score each category
    scores: Counter = Counter()

    for category_key, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            # Use word boundary matching for better accuracy
            pattern = rf"\b{re.escape(keyword)}\b"
            matches = len(re.findall(pattern, text_to_match, re.IGNORECASE))
            if matches:
                scores[category_key] += matches

    if not scores:
        return Category.UNCATEGORIZED

    # Get the category with highest score
    best_category = scores.most_common(1)[0][0]

    # Map to Category enum
    category_map = {
        "tech_startups": Category.TECH_STARTUPS,
        "business_finance": Category.BUSINESS_FINANCE,
        "news_current_events": Category.NEWS_CURRENT_EVENTS,
        "philosophy": Category.PHILOSOPHY,
        "lifestyle_personal_growth": Category.LIFESTYLE_PERSONAL_GROWTH,
        "career_development": Category.CAREER_DEVELOPMENT,
        "health_longevity": Category.HEALTH_LONGEVITY,
        "fitness_weight_training": Category.FITNESS_WEIGHT_TRAINING,
        "sleep_management": Category.SLEEP_MANAGEMENT,
    }

    return category_map.get(best_category, Category.UNCATEGORIZED)


def group_by_category(episodes: List[Episode]) -> Dict[Category, List[Episode]]:
    """Group episodes by their matched category.

    Returns a dictionary with categories as keys and lists of episodes as values.
    Categories are sorted by the number of episodes (descending).
    """
    groups: Dict[Category, List[Episode]] = {}

    for episode in episodes:
        category = episode.matched_category
        if category not in groups:
            groups[category] = []
        groups[category].append(episode)

    # Sort episodes within each category by published date (newest first)
    # Use timestamp for comparison to avoid timezone-aware vs naive comparison issues
    from datetime import datetime
    default_time = datetime(1970, 1, 1)
    for category in groups:
        groups[category].sort(
            key=lambda ep: (ep.published_at.replace(tzinfo=None) if ep.published_at else default_time),
            reverse=True
        )

    return groups

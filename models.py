from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class Category(str, Enum):
    TECH_STARTUPS = "tech_startups"
    BUSINESS_FINANCE = "business_finance"
    NEWS_CURRENT_EVENTS = "news_current_events"
    PHILOSOPHY = "philosophy"
    LIFESTYLE_PERSONAL_GROWTH = "lifestyle_personal_growth"
    CAREER_DEVELOPMENT = "career_development"
    HEALTH_LONGEVITY = "health_longevity"
    FITNESS_WEIGHT_TRAINING = "fitness_weight_training"
    SLEEP_MANAGEMENT = "sleep_management"
    UNCATEGORIZED = "uncategorized"


class Source(str, Enum):
    PODCAST_INDEX = "podcast_index"
    SPOTIFY = "spotify"
    APPLE_PODCASTS = "apple_podcasts"
    LISTEN_NOTES = "listen_notes"


class Podcast(BaseModel):
    """Represents a podcast show."""
    id: str
    title: str
    author: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    feed_url: Optional[str] = None
    website_url: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    source: Source


class Episode(BaseModel):
    """Represents a podcast episode."""
    id: str
    title: str
    podcast_title: str
    podcast_author: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None  # AI-generated summary (future)
    published_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    audio_url: Optional[str] = None
    episode_url: Optional[str] = None
    image_url: Optional[str] = None
    source: Source
    source_categories: List[str] = Field(default_factory=list)
    matched_category: Category = Category.UNCATEGORIZED

    @property
    def duration_formatted(self) -> str:
        """Return duration in HH:MM:SS format."""
        if not self.duration_seconds:
            return "Unknown"
        hours, remainder = divmod(self.duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    class Config:
        # Allow mutation for updating matched_category
        allow_mutation = True


class Newsletter(BaseModel):
    """Represents a generated newsletter."""
    date: datetime
    episodes_by_category: Dict[Category, List[Episode]] = Field(default_factory=dict)
    total_episodes: int = 0
    markdown_content: Optional[str] = None

    def add_episode(self, episode: Episode) -> None:
        """Add an episode to the appropriate category."""
        category = episode.matched_category
        if category not in self.episodes_by_category:
            self.episodes_by_category[category] = []
        self.episodes_by_category[category].append(episode)
        self.total_episodes += 1

    class Config:
        # Allow mutation for add_episode
        allow_mutation = True

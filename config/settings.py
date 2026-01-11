from functools import lru_cache
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Podcast Index API
    podcast_index_api_key: Optional[str] = None
    podcast_index_api_secret: Optional[str] = None

    # Spotify API
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None

    # Resend Email API
    resend_api_key: Optional[str] = None

    # Newsletter settings
    newsletter_email: Optional[str] = None

    # Claude API (for future AI summaries)
    anthropic_api_key: Optional[str] = None

    # Collection settings
    days_to_look_back: int = 3
    max_episodes_per_source: int = 50
    max_episodes_per_category: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def has_podcast_index(self) -> bool:
        return bool(self.podcast_index_api_key and self.podcast_index_api_secret)

    @property
    def has_spotify(self) -> bool:
        return bool(self.spotify_client_id and self.spotify_client_secret)

    @property
    def has_resend(self) -> bool:
        return bool(self.resend_api_key)

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)


# Category keywords for matching episodes to user interests
CATEGORY_KEYWORDS = {
    "tech_startups": [
        "tech", "technology", "startup", "startups", "entrepreneur", "silicon valley",
        "software", "programming", "developer", "coding", "ai", "artificial intelligence",
        "machine learning", "data science", "venture capital", "vc", "saas", "product",
        "innovation", "disruption", "founder", "ceo", "cto", "engineering",
    ],
    "philosophy": [
        "philosophy", "philosophical", "ethics", "moral", "meaning", "existence",
        "consciousness", "wisdom", "stoic", "stoicism", "meditation", "mindfulness",
        "buddhism", "zen", "spiritual", "metaphysics", "epistemology",
    ],
    "lifestyle_personal_growth": [
        "lifestyle", "personal growth", "self-improvement", "self-help", "habits",
        "productivity", "motivation", "inspiration", "happiness", "relationships",
        "dating", "marriage", "parenting", "family", "minimalism", "creativity",
    ],
    "career_development": [
        "career", "job", "employment", "professional", "work", "workplace",
        "interview", "resume", "networking", "promotion", "salary", "negotiation",
        "remote work", "freelance", "side hustle", "skill", "learning",
    ],
    "health_longevity": [
        "health", "longevity", "aging", "anti-aging", "lifespan", "wellness",
        "nutrition", "diet", "fasting", "supplement", "biohacking", "medical",
        "doctor", "disease", "prevention", "immune", "gut health", "mental health",
    ],
    "fitness_weight_training": [
        "fitness", "weight training", "weightlifting", "strength", "muscle",
        "bodybuilding", "gym", "workout", "exercise", "lifting", "powerlifting",
        "crossfit", "running", "cardio", "sports", "athletic", "performance",
    ],
    "sleep_management": [
        "sleep", "insomnia", "rest", "recovery", "circadian", "melatonin",
        "dream", "nap", "fatigue", "energy", "tired", "bedtime",
    ],
}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

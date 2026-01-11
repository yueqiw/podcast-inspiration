from abc import ABC, abstractmethod
from typing import Optional, List
import logging

from models import Episode, Source
from config.settings import Settings

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for podcast collectors."""

    source: Source

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the collector has required API credentials."""
        pass

    @abstractmethod
    def collect(self, max_episodes: Optional[int] = None) -> List[Episode]:
        """Collect episodes from the source.

        Args:
            max_episodes: Maximum number of episodes to collect.
                         Defaults to settings.max_episodes_per_source.

        Returns:
            List of Episode objects.
        """
        pass

    def safe_collect(self, max_episodes: Optional[int] = None) -> List[Episode]:
        """Safely collect episodes, handling errors gracefully."""
        if not self.is_configured():
            self.logger.warning(f"{self.source.value} collector is not configured, skipping")
            return []

        try:
            episodes = self.collect(max_episodes)
            self.logger.info(f"Collected {len(episodes)} episodes from {self.source.value}")
            return episodes
        except Exception as e:
            self.logger.error(f"Error collecting from {self.source.value}: {e}")
            return []

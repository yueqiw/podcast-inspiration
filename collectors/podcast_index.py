import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, List

import requests

from models import Episode, Source
from config.settings import Settings
from .base import BaseCollector


class PodcastIndexCollector(BaseCollector):
    """Collector for Podcast Index API (podcastindex.org)."""

    source = Source.PODCAST_INDEX
    BASE_URL = "https://api.podcastindex.org/api/1.0"

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self._session = requests.Session()

    def is_configured(self) -> bool:
        return self.settings.has_podcast_index

    def _get_headers(self) -> dict:
        """Generate authentication headers for Podcast Index API."""
        api_key = self.settings.podcast_index_api_key
        api_secret = self.settings.podcast_index_api_secret

        epoch_time = int(time.time())
        data_to_hash = api_key + api_secret + str(epoch_time)
        sha1_hash = hashlib.sha1(data_to_hash.encode("utf-8")).hexdigest()

        return {
            "X-Auth-Date": str(epoch_time),
            "X-Auth-Key": api_key,
            "Authorization": sha1_hash,
            "User-Agent": "PodcastNewsletter/1.0",
        }

    def _make_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make authenticated request to Podcast Index API."""
        url = f"{self.BASE_URL}/{endpoint}"
        response = self._session.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()
        return response.json()

    def collect(self, max_episodes: Optional[int] = None) -> List[Episode]:
        """Collect trending and recent episodes from Podcast Index."""
        max_episodes = max_episodes or self.settings.max_episodes_per_source
        episodes = []

        # Get trending podcasts
        try:
            trending = self._make_request("podcasts/trending", {"max": 20})
            for feed in trending.get("feeds", [])[:10]:
                feed_episodes = self._get_episodes_from_feed(feed["id"])
                episodes.extend(feed_episodes[:3])  # Top 3 episodes per feed
        except Exception as e:
            self.logger.error(f"Error fetching trending: {e}")

        # Get recent episodes
        try:
            since = int((datetime.now() - timedelta(days=self.settings.days_to_look_back)).timestamp())
            recent = self._make_request("recent/episodes", {"since": since, "max": max_episodes})
            for item in recent.get("items", []):
                episode = self._parse_episode(item)
                if episode:
                    episodes.append(episode)
        except Exception as e:
            self.logger.error(f"Error fetching recent episodes: {e}")

        return episodes[:max_episodes]

    def _get_episodes_from_feed(self, feed_id: int) -> List[Episode]:
        """Get episodes from a specific podcast feed."""
        try:
            response = self._make_request("episodes/byfeedid", {"id": feed_id, "max": 5})
            episodes = []
            for item in response.get("items", []):
                episode = self._parse_episode(item)
                if episode:
                    episodes.append(episode)
            return episodes
        except Exception as e:
            self.logger.error(f"Error fetching feed {feed_id}: {e}")
            return []

    def _parse_episode(self, item: dict) -> Optional[Episode]:
        """Parse Podcast Index episode data into Episode model."""
        try:
            published_at = None
            if item.get("datePublished"):
                published_at = datetime.fromtimestamp(item["datePublished"])

            return Episode(
                id=f"pi_{item.get('id', '')}",
                title=item.get("title", "Untitled"),
                podcast_title=item.get("feedTitle", "Unknown Podcast"),
                podcast_author=item.get("feedAuthor"),
                description=item.get("description", ""),
                published_at=published_at,
                duration_seconds=item.get("duration"),
                audio_url=item.get("enclosureUrl"),
                episode_url=item.get("link"),
                image_url=item.get("feedImage") or item.get("image"),
                source=self.source,
                source_categories=item.get("categories", {}).values() if isinstance(item.get("categories"), dict) else [],
            )
        except Exception as e:
            self.logger.error(f"Error parsing episode: {e}")
            return None

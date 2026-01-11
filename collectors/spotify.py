from datetime import datetime
from typing import Optional, List

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from models import Episode, Source
from config.settings import Settings
from .base import BaseCollector


class SpotifyCollector(BaseCollector):
    """Collector for Spotify Podcasts API."""

    source = Source.SPOTIFY

    # Popular podcast categories on Spotify
    SEARCH_QUERIES = [
        "top podcasts 2025",
        "trending technology podcast",
        "business podcast",
        "news podcast daily",
        "health wellness podcast",
        "self improvement podcast",
        "philosophy podcast",
        "fitness workout podcast",
    ]

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self._client: Optional[spotipy.Spotify] = None

    def is_configured(self) -> bool:
        return self.settings.has_spotify

    def _get_client(self) -> spotipy.Spotify:
        """Get or create Spotify client."""
        if self._client is None:
            auth_manager = SpotifyClientCredentials(
                client_id=self.settings.spotify_client_id,
                client_secret=self.settings.spotify_client_secret,
            )
            self._client = spotipy.Spotify(auth_manager=auth_manager)
        return self._client

    def collect(self, max_episodes: Optional[int] = None) -> List[Episode]:
        """Collect episodes by searching Spotify for popular podcasts."""
        max_episodes = max_episodes or self.settings.max_episodes_per_source
        episodes = []
        seen_show_ids = set()

        client = self._get_client()

        for query in self.SEARCH_QUERIES:
            try:
                # Search for shows
                results = client.search(q=query, type="show", limit=5, market="US")
                for show in results.get("shows", {}).get("items", []):
                    if not show or show["id"] in seen_show_ids:
                        continue
                    seen_show_ids.add(show["id"])

                    # Get recent episodes from this show
                    show_episodes = self._get_show_episodes(client, show)
                    episodes.extend(show_episodes)

                    if len(episodes) >= max_episodes:
                        break
            except Exception as e:
                self.logger.error(f"Error searching Spotify for '{query}': {e}")

            if len(episodes) >= max_episodes:
                break

        return episodes[:max_episodes]

    def _get_show_episodes(self, client: spotipy.Spotify, show: dict) -> List[Episode]:
        """Get recent episodes from a Spotify show."""
        episodes = []
        try:
            show_episodes = client.show_episodes(show["id"], limit=3, market="US")
            for item in show_episodes.get("items", []):
                episode = self._parse_episode(item, show)
                if episode:
                    episodes.append(episode)
        except Exception as e:
            self.logger.error(f"Error fetching episodes for show {show.get('name')}: {e}")
        return episodes

    def _parse_episode(self, item: dict, show: dict) -> Optional[Episode]:
        """Parse Spotify episode data into Episode model."""
        try:
            published_at = None
            if item.get("release_date"):
                try:
                    published_at = datetime.strptime(item["release_date"], "%Y-%m-%d")
                except ValueError:
                    pass

            # Get best available image
            image_url = None
            images = item.get("images") or show.get("images", [])
            if images:
                image_url = images[0].get("url")

            return Episode(
                id=f"sp_{item.get('id', '')}",
                title=item.get("name", "Untitled"),
                podcast_title=show.get("name", "Unknown Podcast"),
                podcast_author=show.get("publisher"),
                description=item.get("description", ""),
                published_at=published_at,
                duration_seconds=item.get("duration_ms", 0) // 1000 if item.get("duration_ms") else None,
                audio_url=item.get("audio_preview_url"),
                episode_url=item.get("external_urls", {}).get("spotify"),
                image_url=image_url,
                source=self.source,
                source_categories=[],
            )
        except Exception as e:
            self.logger.error(f"Error parsing Spotify episode: {e}")
            return None

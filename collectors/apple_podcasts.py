from datetime import datetime
from typing import Optional, List
from xml.etree import ElementTree

import requests

from models import Episode, Source
from config.settings import Settings
from .base import BaseCollector


class ApplePodcastsCollector(BaseCollector):
    """Collector for Apple Podcasts top charts via RSS feeds and iTunes API."""

    source = Source.APPLE_PODCASTS

    # Apple Podcasts genre IDs
    GENRE_IDS = {
        "technology": 1318,
        "business": 1321,
        "news": 1489,
        "health_fitness": 1512,
        "society_culture": 1324,
        "education": 1304,
        "science": 1533,
        "sports": 1545,
    }

    LOOKUP_API = "https://itunes.apple.com/lookup"
    TOP_PODCASTS_API = "https://itunes.apple.com/us/rss/toppodcasts/limit={limit}/genre={genre}/json"

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "PodcastNewsletter/1.0"})

    def is_configured(self) -> bool:
        # Apple Podcasts doesn't require API keys
        return True

    def collect(self, max_episodes: Optional[int] = None) -> List[Episode]:
        """Collect episodes from Apple Podcasts top charts."""
        max_episodes = max_episodes or self.settings.max_episodes_per_source
        episodes = []
        seen_podcast_ids = set()

        for genre_name, genre_id in self.GENRE_IDS.items():
            try:
                top_podcasts = self._get_top_podcasts(genre_id, limit=10)
                for podcast in top_podcasts:
                    podcast_id = podcast.get("id", {}).get("attributes", {}).get("im:id")
                    if not podcast_id or podcast_id in seen_podcast_ids:
                        continue
                    seen_podcast_ids.add(podcast_id)

                    # Get feed URL and fetch episodes
                    feed_url = self._get_feed_url(podcast_id)
                    if feed_url:
                        podcast_episodes = self._get_episodes_from_feed(feed_url, podcast, genre_name)
                        episodes.extend(podcast_episodes[:2])  # Top 2 episodes per podcast

                    if len(episodes) >= max_episodes:
                        break
            except Exception as e:
                self.logger.error(f"Error fetching Apple Podcasts genre {genre_name}: {e}")

            if len(episodes) >= max_episodes:
                break

        return episodes[:max_episodes]

    def _get_top_podcasts(self, genre_id: int, limit: int = 10) -> List[dict]:
        """Get top podcasts for a genre from Apple's RSS feed."""
        url = self.TOP_PODCASTS_API.format(limit=limit, genre=genre_id)
        try:
            response = self._session.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("feed", {}).get("entry", [])
        except Exception as e:
            self.logger.error(f"Error fetching top podcasts: {e}")
            return []

    def _get_feed_url(self, podcast_id: str) -> Optional[str]:
        """Get RSS feed URL for a podcast using iTunes Lookup API."""
        try:
            response = self._session.get(self.LOOKUP_API, params={"id": podcast_id, "entity": "podcast"})
            response.raise_for_status()
            results = response.json().get("results", [])
            if results:
                return results[0].get("feedUrl")
        except Exception as e:
            self.logger.error(f"Error looking up podcast {podcast_id}: {e}")
        return None

    def _get_episodes_from_feed(self, feed_url: str, podcast_info: dict, genre: str) -> List[Episode]:
        """Parse RSS feed to get episodes."""
        episodes = []
        try:
            response = self._session.get(feed_url, timeout=10)
            response.raise_for_status()

            root = ElementTree.fromstring(response.content)
            channel = root.find("channel")
            if channel is None:
                return []

            podcast_title = channel.findtext("title", "Unknown Podcast")
            podcast_author = channel.findtext("{http://www.itunes.com/dtds/podcast-1.0.dtd}author", "")
            podcast_image = None
            image_elem = channel.find("{http://www.itunes.com/dtds/podcast-1.0.dtd}image")
            if image_elem is not None:
                podcast_image = image_elem.get("href")

            for item in channel.findall("item")[:5]:
                episode = self._parse_rss_item(item, podcast_title, podcast_author, podcast_image, genre)
                if episode:
                    episodes.append(episode)

        except Exception as e:
            self.logger.error(f"Error parsing feed {feed_url}: {e}")

        return episodes

    def _parse_rss_item(
        self,
        item: ElementTree.Element,
        podcast_title: str,
        podcast_author: str,
        podcast_image: Optional[str],
        genre: str,
    ) -> Optional[Episode]:
        """Parse RSS item into Episode model."""
        try:
            # Parse publication date
            published_at = None
            pub_date = item.findtext("pubDate")
            if pub_date:
                try:
                    # Handle various date formats
                    for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"]:
                        try:
                            published_at = datetime.strptime(pub_date.strip(), fmt)
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass

            # Get duration
            duration_seconds = None
            duration_str = item.findtext("{http://www.itunes.com/dtds/podcast-1.0.dtd}duration")
            if duration_str:
                duration_seconds = self._parse_duration(duration_str)

            # Get audio URL
            audio_url = None
            enclosure = item.find("enclosure")
            if enclosure is not None:
                audio_url = enclosure.get("url")

            # Get episode image or fall back to podcast image
            image_url = podcast_image
            ep_image = item.find("{http://www.itunes.com/dtds/podcast-1.0.dtd}image")
            if ep_image is not None:
                image_url = ep_image.get("href") or image_url

            # Generate unique ID from guid or title
            guid = item.findtext("guid") or item.findtext("title", "")
            episode_id = f"ap_{hash(guid) % 10**10}"

            return Episode(
                id=episode_id,
                title=item.findtext("title", "Untitled"),
                podcast_title=podcast_title,
                podcast_author=podcast_author,
                description=item.findtext("description", "") or item.findtext("{http://www.itunes.com/dtds/podcast-1.0.dtd}summary", ""),
                published_at=published_at,
                duration_seconds=duration_seconds,
                audio_url=audio_url,
                episode_url=item.findtext("link"),
                image_url=image_url,
                source=self.source,
                source_categories=[genre],
            )
        except Exception as e:
            self.logger.error(f"Error parsing RSS item: {e}")
            return None

    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse duration string to seconds."""
        try:
            parts = duration_str.split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            else:
                return int(duration_str)
        except (ValueError, TypeError):
            return None

from datetime import datetime
from typing import Optional, List

import requests
from bs4 import BeautifulSoup

from models import Episode, Source
from config.settings import Settings
from .base import BaseCollector


class ListenNotesCollector(BaseCollector):
    """Collector for Listen Notes via web scraping."""

    source = Source.LISTEN_NOTES
    BASE_URL = "https://www.listennotes.com"

    # Listen Notes best podcasts pages by category
    CATEGORY_PAGES = {
        "technology": "/best-technology-podcasts",
        "business": "/best-business-podcasts",
        "news": "/best-news-podcasts",
        "health": "/best-health-fitness-podcasts",
        "education": "/best-education-podcasts",
        "society": "/best-society-culture-podcasts",
        "science": "/best-science-podcasts",
    }

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })

    def is_configured(self) -> bool:
        # Web scraping doesn't require API keys
        return True

    def collect(self, max_episodes: Optional[int] = None) -> List[Episode]:
        """Collect episodes by scraping Listen Notes."""
        max_episodes = max_episodes or self.settings.max_episodes_per_source
        episodes = []

        # Try to get trending podcasts first
        try:
            trending_episodes = self._scrape_trending()
            episodes.extend(trending_episodes)
        except Exception as e:
            self.logger.error(f"Error scraping trending: {e}")

        # Then get from category pages
        for category, path in self.CATEGORY_PAGES.items():
            if len(episodes) >= max_episodes:
                break
            try:
                category_episodes = self._scrape_category_page(path, category)
                episodes.extend(category_episodes)
            except Exception as e:
                self.logger.error(f"Error scraping category {category}: {e}")

        return episodes[:max_episodes]

    def _scrape_trending(self) -> List[Episode]:
        """Scrape trending podcasts from Listen Notes homepage."""
        episodes = []
        try:
            response = self._session.get(f"{self.BASE_URL}/", timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Look for podcast cards on the page
            podcast_cards = soup.select(".podcast-card, .ln-card, [class*='podcast']")[:10]

            for card in podcast_cards:
                episode = self._parse_podcast_card(card)
                if episode:
                    episodes.append(episode)

        except Exception as e:
            self.logger.error(f"Error scraping trending: {e}")

        return episodes

    def _scrape_category_page(self, path: str, category: str) -> List[Episode]:
        """Scrape a category best podcasts page."""
        episodes = []
        try:
            response = self._session.get(f"{self.BASE_URL}{path}", timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Find podcast entries
            podcast_entries = soup.select(".ln-shadow-card, .podcast-card, [class*='podcast-item']")[:10]

            for entry in podcast_entries:
                episode = self._parse_podcast_card(entry, category)
                if episode:
                    episodes.append(episode)

        except Exception as e:
            self.logger.error(f"Error scraping {path}: {e}")

        return episodes

    def _parse_podcast_card(self, card, category: str = "") -> Optional[Episode]:
        """Parse a podcast card element into Episode model."""
        try:
            # Try various selectors to find title
            title_elem = card.select_one("h2, h3, h4, .title, [class*='title']")
            title = title_elem.get_text(strip=True) if title_elem else None

            if not title:
                return None

            # Try to find podcast name
            podcast_elem = card.select_one(".podcast-name, [class*='podcast-name'], .subtitle")
            podcast_title = podcast_elem.get_text(strip=True) if podcast_elem else "Unknown Podcast"

            # Try to find description
            desc_elem = card.select_one(".description, [class*='description'], p")
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            # Try to find link
            link_elem = card.select_one("a[href]")
            episode_url = None
            if link_elem:
                href = link_elem.get("href", "")
                if href.startswith("/"):
                    episode_url = f"{self.BASE_URL}{href}"
                elif href.startswith("http"):
                    episode_url = href

            # Try to find image
            img_elem = card.select_one("img")
            image_url = img_elem.get("src") if img_elem else None

            # Generate unique ID
            episode_id = f"ln_{hash(title + podcast_title) % 10**10}"

            return Episode(
                id=episode_id,
                title=title,
                podcast_title=podcast_title,
                description=description,
                published_at=None,  # Not always available on category pages
                episode_url=episode_url,
                image_url=image_url,
                source=self.source,
                source_categories=[category] if category else [],
            )
        except Exception as e:
            self.logger.error(f"Error parsing podcast card: {e}")
            return None

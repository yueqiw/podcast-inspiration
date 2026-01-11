#!/usr/bin/env python3
"""
Podcast Inspiration - Newsletter Generator

Collects, curates, and delivers podcast recommendations.

Usage:
    python main.py                    # Full pipeline: collect, generate, archive
    python main.py --collect-only     # Only collect podcasts (no output)
    python main.py --generate-only    # Generate from cached data
    python main.py --send             # Generate and send email
    python main.py --test-email       # Send a test email
    python main.py --status           # Show configuration status
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from models import Newsletter, Category
from config.settings import get_settings
from collectors import (
    PodcastIndexCollector,
    SpotifyCollector,
    ApplePodcastsCollector,
    ListenNotesCollector,
)
from processors import normalize_episodes, deduplicate_episodes, categorize_episodes
from processors.categorizer import group_by_category
from output import generate_newsletter, send_newsletter, archive_newsletter
from output.email_sender import send_test_email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def collect_episodes(settings) -> list:
    """Collect episodes from all configured sources."""
    logger.info("Starting episode collection...")

    collectors = [
        PodcastIndexCollector(settings),
        SpotifyCollector(settings),
        ApplePodcastsCollector(settings),
        ListenNotesCollector(settings),
    ]

    all_episodes = []
    for collector in collectors:
        episodes = collector.safe_collect()
        all_episodes.extend(episodes)
        logger.info(f"  {collector.source.value}: {len(episodes)} episodes")

    logger.info(f"Total collected: {len(all_episodes)} episodes")
    return all_episodes


def process_episodes(episodes: list) -> list:
    """Process collected episodes through the pipeline."""
    logger.info("Processing episodes...")

    # Normalize
    normalized = normalize_episodes(episodes)
    logger.info(f"  After normalization: {len(normalized)} episodes")

    # Deduplicate
    deduplicated = deduplicate_episodes(normalized)
    logger.info(f"  After deduplication: {len(deduplicated)} episodes")

    # Categorize
    categorized = categorize_episodes(deduplicated)
    logger.info(f"  After categorization: {len(categorized)} episodes")

    return categorized


def create_newsletter(episodes: list, settings) -> Newsletter:
    """Create a newsletter from processed episodes."""
    logger.info("Creating newsletter...")

    newsletter = Newsletter(date=datetime.now())

    # Group by category and limit per category
    grouped = group_by_category(episodes)

    for category, cat_episodes in grouped.items():
        # Limit episodes per category
        limited = cat_episodes[:settings.max_episodes_per_category]
        for episode in limited:
            newsletter.add_episode(episode)

    # Generate markdown content
    newsletter.markdown_content = generate_newsletter(newsletter)

    logger.info(f"Newsletter created with {newsletter.total_episodes} episodes")
    return newsletter


def show_status(settings):
    """Display configuration status."""
    print("\n=== Podcast Inspiration Configuration ===\n")

    print("Data Sources:")
    print(f"  Podcast Index: {'Configured' if settings.has_podcast_index else 'Not configured'}")
    print(f"  Spotify:       {'Configured' if settings.has_spotify else 'Not configured'}")
    print(f"  Apple Podcasts: Always available (no API key needed)")
    print(f"  Listen Notes:   Always available (web scraping)")

    print("\nEmail Delivery:")
    print(f"  Resend API:    {'Configured' if settings.has_resend else 'Not configured'}")
    print(f"  Recipient:     {settings.newsletter_email or 'Not set'}")

    print("\nAI Features:")
    print(f"  Claude API:    {'Configured' if settings.has_anthropic else 'Not configured (optional)'}")

    print("\nSettings:")
    print(f"  Days to look back:     {settings.days_to_look_back}")
    print(f"  Max episodes/source:   {settings.max_episodes_per_source}")
    print(f"  Max episodes/category: {settings.max_episodes_per_category}")

    print("\n" + "=" * 43 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Podcast Inspiration - Newsletter Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--collect-only",
        action="store_true",
        help="Only collect episodes, don't generate output",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send newsletter via email after generating",
    )
    parser.add_argument(
        "--test-email",
        action="store_true",
        help="Send a test email to verify configuration",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show configuration status",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    settings = get_settings()

    # Show status
    if args.status:
        show_status(settings)
        return 0

    # Test email
    if args.test_email:
        print("Sending test email...")
        if send_test_email(settings):
            print("Test email sent successfully!")
            return 0
        else:
            print("Failed to send test email. Check your configuration.")
            return 1

    # Main pipeline
    try:
        # Collect
        episodes = collect_episodes(settings)
        if not episodes:
            logger.warning("No episodes collected. Check your API configurations.")
            return 1

        if args.collect_only:
            print(f"\nCollected {len(episodes)} episodes.")
            return 0

        # Process
        processed = process_episodes(episodes)
        if not processed:
            logger.warning("No episodes after processing.")
            return 1

        # Create newsletter
        newsletter = create_newsletter(processed, settings)

        # Archive locally
        filepath = archive_newsletter(newsletter)
        print(f"\nNewsletter saved to: {filepath}")

        # Send email if requested
        if args.send:
            print("Sending newsletter via email...")
            if send_newsletter(newsletter, settings):
                print("Email sent successfully!")
            else:
                print("Failed to send email. Newsletter was still saved locally.")

        # Print summary
        print(f"\n=== Newsletter Summary ===")
        print(f"Date: {newsletter.date.strftime('%B %d, %Y')}")
        print(f"Total episodes: {newsletter.total_episodes}")
        print("\nEpisodes by category:")
        for category in newsletter.episodes_by_category:
            count = len(newsletter.episodes_by_category[category])
            from output.markdown_generator import CATEGORY_NAMES
            print(f"  {CATEGORY_NAMES[category]}: {count}")

        return 0

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        return 130
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

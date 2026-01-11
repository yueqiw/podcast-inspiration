# Podcast Inspiration

A Python tool that aggregates popular podcasts from multiple sources, curates them by topic, and delivers a newsletter via email.

## Features

- **Multi-source collection**: Fetches podcasts from Podcast Index API, Apple Podcasts charts, Spotify, and Listen Notes
- **Smart categorization**: Automatically categorizes episodes into topics like Tech, Health, Fitness, Philosophy, and more
- **Deduplication**: Removes duplicate episodes across sources
- **Dual output**: Generates both markdown files and HTML emails
- **Email delivery**: Sends newsletters via Resend API

## Categories

- Tech & Startups
- Health & Longevity
- Fitness & Weight Training
- Sleep Management
- Lifestyle & Personal Growth
- Career Development
- Philosophy

## Installation

```bash
# Clone the repository
git clone https://github.com/yueqiw/podcast-inspiration.git
cd podcast-inspiration

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

## Configuration

Edit `.env` with your API credentials:

```bash
# Podcast Index API (free at https://podcastindex.org/signup)
PODCAST_INDEX_API_KEY=your_key
PODCAST_INDEX_API_SECRET=your_secret

# Spotify API (optional, https://developer.spotify.com/dashboard)
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret

# Resend Email API (https://resend.com)
RESEND_API_KEY=your_resend_key
NEWSLETTER_EMAIL=your_email@example.com
```

**Note**: Apple Podcasts works without any API keys.

## Usage

```bash
# Check configuration status
python main.py --status

# Generate newsletter (saves to newsletters/ folder)
python main.py

# Generate and send via email
python main.py --send

# Send a test email
python main.py --test-email

# Only collect podcasts (no output)
python main.py --collect-only
```

## Project Structure

```
podcast_inspiration/
├── main.py                 # CLI entry point
├── models.py               # Pydantic data models
├── requirements.txt        # Python dependencies
├── collectors/             # Data source collectors
│   ├── podcast_index.py    # Podcast Index API
│   ├── spotify.py          # Spotify API
│   ├── apple_podcasts.py   # Apple Podcasts charts
│   └── listen_notes.py     # Listen Notes scraping
├── processors/             # Data processing pipeline
│   ├── normalizer.py       # Clean and normalize data
│   ├── deduplicator.py     # Remove duplicates
│   └── categorizer.py      # Match to categories
├── output/                 # Newsletter generation
│   ├── markdown_generator.py
│   ├── email_sender.py
│   └── archiver.py
├── config/
│   └── settings.py         # Configuration and keywords
└── newsletters/            # Generated newsletters (git-ignored)
```

## Scheduling (Optional)

To run automatically every other day, add a cron job:

```bash
crontab -e

# Add this line (runs at 8am every other day):
0 8 */2 * * cd /path/to/podcast-inspiration && python3 main.py --send
```

## Sample Output

```markdown
# Podcast Inspiration - January 10, 2026

*18 episodes curated for you*

## Tech & Startups

*The latest on AI breakthroughs, startup strategies, and emerging technologies.*

### Building a Personal AI Model Map
**The AI Daily Brief** by Nathaniel Whittemore
*Jan 10, 2026 | 12:17*

This episode walks through the "model mapping" challenge...
```

## License

MIT

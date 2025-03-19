import os
import json
import datetime
import sys

# Fix import paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))  # Add parent directory to path

# Now use the correct imports
from src.utils import ensure_dir_exists
from src.translation import detect_language
import feedparser

def fetch_rss_articles(rss_url, num_articles=5, since_date=None):
    """
    Fetch articles from an RSS feed

    Parameters:
    - rss_url: URL of the RSS feed
    - num_articles: Number of articles to fetch (default: 5)
    - since_date: Only fetch articles published after this date (default: None)

    Returns:
    - List of dictionaries containing article details
    """
    try:
        # Parse the feed
        feed = feedparser.parse(rss_url)

        # Check if feed parsing was successful
        if not hasattr(feed, 'entries') or len(feed.entries) == 0:
            print(f"Error parsing RSS feed from {rss_url} or feed is empty")
            return []

        # Initialize empty list for articles
        articles = []

        # Process feed entries
        for entry in feed.entries:
            # Get publication date
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime.datetime(*entry.published_parsed[:6])
            else:
                # Try other common date fields
                for date_field in ['updated_parsed', 'created_parsed']:
                    if hasattr(entry, date_field) and getattr(entry, date_field):
                        pub_date = datetime.datetime(*getattr(entry, date_field)[:6])
                        break
                else:
                    pub_date = datetime.datetime.now()  # Default to current time if no date available

            # Skip if article is older than since_date
            if since_date and pub_date < since_date:
                continue

            # Extract content field (might be in different attributes depending on RSS feed)
            content = ""
            if hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description
            elif hasattr(entry, 'content'):
                # Some feeds have content in a list of dictionaries
                for content_item in entry.content:
                    if 'value' in content_item:
                        content = content_item['value']
                        break

            # Create article dictionary
            article = {
                'title': entry.title,
                'summary': content,
                'link': entry.link if hasattr(entry, 'link') else "",
                'published': pub_date.isoformat(),
            }

            articles.append(article)

            # Break if we have enough articles
            if len(articles) >= num_articles:
                break

        return articles

    except Exception as e:
        print(f"Error fetching RSS feed: {e}")
        return []

def process_news_for_kids(rss_url, num_articles=5, since_date=None):
    """
    Main function to fetch, process, and prepare news for kids

    Parameters:
    - rss_url: URL of the RSS feed
    - num_articles: Number of articles to fetch (default: 5)
    - since_date: Only fetch articles published after this date (default: None)

    Returns:
    - List of processed articles
    """
    # Fetch articles
    print(f"Fetching news articles from {rss_url}...")
    articles = fetch_rss_articles(rss_url, num_articles, since_date)

    if not articles:
        print("No articles found.")
        return []

    # Process each article
    processed_articles = []

    print(f"Processing {len(articles)} articles...")
    for i, article in enumerate(articles):
        print(f"Article {i+1}: {article['title']}")

        # Create a processed article
        processed_article = {
            'original_title': article['title'],
            'original_summary': article['summary'],
            'link': article['link'],
            'published': article['published']
        }

        # Detect title language but don't translate yet
        title_lang = detect_language(article['title'])
        processed_article['title_language'] = title_lang

        # Initially set Tamil title to same as original (will be translated later if needed)
        processed_article['tamil_title'] = article['title']

        # Detect summary language but don't translate yet
        if article['summary']:
            summary_lang = detect_language(article['summary'])
            processed_article['summary_language'] = summary_lang
            processed_article['tamil_summary'] = article['summary']
        else:
            processed_article['tamil_summary'] = ""
            processed_article['summary_language'] = "unknown"

        # Set needs_translation flag based on detected languages
        processed_article['needs_translation'] = (
            (title_lang != "ta" and title_lang != "unknown") or
            (processed_article['summary_language'] != "ta" and 
             processed_article['summary_language'] != "unknown")
        )

        processed_articles.append(processed_article)

    return processed_articles

def save_processed_articles(articles, filename="data/processed_news.json"):
    """
    Save processed articles to a JSON file

    Parameters:
    - articles: List of processed articles
    - filename: Output filename (default: "data/processed_news.json")
    """
    ensure_dir_exists(os.path.dirname(filename))
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(articles)} articles to {filename}")

def main():
    # Example RSS feed URLs (modify as needed)
    rss_urls = [
        "https://www.thehindu.com/news/national/feeder/default.rss",  # English - National news
        "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms",  # English - India news
        "https://tamil.oneindia.com/rss/tamil-news.xml",              # Tamil news
        # Add more RSS feeds as needed
    ]

    # Optional: Filter by date (e.g., only articles from the last day)
    # since_date = datetime.datetime.now() - datetime.timedelta(days=1)
    since_date = None

    all_processed_articles = []

    # Process each RSS feed
    for url in rss_urls:
        articles = process_news_for_kids(url, num_articles=2,  # Reduced to 2 for faster testing
                                        since_date=since_date)
        all_processed_articles.extend(articles)

    # Save results
    save_processed_articles(all_processed_articles)

    # Print results
    print("\nProcessed News Articles:")
    for i, article in enumerate(all_processed_articles):
        print(f"\n{i+1}. {article['original_title']}")
        print(f"   Language: {article['title_language']}")
        print(f"   Needs Translation: {'Yes' if article['needs_translation'] else 'No'}")

if __name__ == "__main__":
    main()
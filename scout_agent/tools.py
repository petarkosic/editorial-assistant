import datetime
import feedparser
from bs4 import BeautifulSoup
from typing import List
from models import NewsArticle

def extract_hrefs_from_description(description: str) -> List[str]:
    if not description:
        return []

    soup = BeautifulSoup(description, 'html.parser')
    hrefs = [a['href'] for a in soup.find_all('a') if a.has_attr('href')]
    
    return hrefs

class NewsFetcherTool:
    """Tool to fetch news from RSS feeds"""

    @staticmethod
    def fetch_news_from_rss(rss_url: str, max_articles: int = 5) -> List[NewsArticle]:
        """Fetch news articles from an RSS feed"""

        feed = feedparser.parse(rss_url)

        if feed.entries is None:
            print("No news articles found in the feed.")
            
            return []
        
        articles = []

        for i, entry in enumerate(feed.entries[:max_articles]):
            if i >= max_articles:
                break

            article = NewsArticle(
                title=entry.title,
                link=entry.link,
                pub_date=datetime.datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else None,
                source=entry.source.title if hasattr(entry, 'source') else "Unknown",
                description=extract_hrefs_from_description(entry.description if hasattr(entry, 'description') else None)
            )

            articles.append(article)

        return articles
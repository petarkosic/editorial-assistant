import datetime
import feedparser
from typing import List
from models import NewsArticle

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
                description=entry.description if hasattr(entry, 'description') else None
            )

            articles.append(article)

        return articles
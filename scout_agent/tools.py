import feedparser
import requests
from typing import List
from models import NewsArticle

class NewsFetcherTool:
    """Tool to fetch news from RSS feeds"""
    
    @staticmethod
    def fetch_news_from_rss(rss_url: str, max_articles: int = 10) -> List[NewsArticle]:
        """Fetch news articles from an RSS feed"""

        feed = feedparser.parse(rss_url)

        articles = []
        
        for i, entry in enumerate(feed.entries):
            if i >= max_articles:
                break
                
            article = NewsArticle(
                title=entry.title,
                link=entry.link,
                pub_date=entry.published_parsed if hasattr(entry, 'published_parsed') else None,
                source=entry.source.title if hasattr(entry, 'source') else "Unknown",
                description=entry.description if hasattr(entry, 'description') else None
            )
            articles.append(article)

        return articles

class NewsAPITool:
    """Tool to fetch news from NewsAPI"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
    
    def fetch_top_headlines(self, category: str = "general", country: str = "us") -> List[NewsArticle]:
        """Fetch top headlines from NewsAPI"""
        url = f"{self.base_url}/top-headlines"
        params = {
            "category": category,
            "country": country,
            "apiKey": self.api_key
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        articles = []
        for item in data.get("articles", []):
            article = NewsArticle(
                title=item["title"],
                link=item["url"],
                pub_date=item["publishedAt"],
                source=item["source"]["name"],
                description=item["description"]
            )
            articles.append(article)
            
        return articles
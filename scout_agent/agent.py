import os
import openai
import json
from typing import List
from models import NewsArticle, AnalysisResult, ScoutReport
from tools import NewsFetcherTool
from datetime import datetime
from googlenewsdecoder import gnewsdecoder

class NewsScoutAgent:
    """AI agent for scouting and analyzing news articles"""
    
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        openai.base_url = os.getenv("OPENAI_API_BASE_URL")
        self.news_fetcher = NewsFetcherTool()
        
    def analyze_articles(self, articles: List[NewsArticle]) -> List[AnalysisResult]:
        """Analyze a batch of articles using AI"""

        articles_data = []
        for i, article in enumerate(articles):
            articles_data.append({
                "title": article.title,
                "link": article.link,
                "source": article.source,
                "pub_date": article.pub_date.isoformat() if article.pub_date else "Unknown",
                "description": article.description
            })
        
        system_prompt = """You are an assistant editor at a major news organization. Your sole task is to monitor incoming news feeds and identify the most important and breaking stories.

        INSTRUCTIONS:
        1. Analyze the provided list of recent news articles.
        2. Ignore minor updates, trivial stories, and redundant information. Focus on impact, novelty, and public interest.
        3. For each article that is important or breaking news (importance_score >= 5):
            - Provide a RELEVANCE SCORE from 1-10 (10 is most important).
            - Write a concise ONE-SENTENCE SUMMARY of the story's significance.
            - Include brief reasoning for your score.
        4. Return your analysis as a valid JSON array of objects.

        JSON FORMAT:
        [
          {
            "importance_score": 8,
            "summary": "A concise sentence explaining the story's impact and why it matters.",
            "original_title": "The original headline here",
            "original_link": "The original link here",
            "reasoning": "Brief explanation of why this score was assigned",
            "description": ["Link to related news articles"]
          }
        ]
        """
        
        user_prompt = f"Please analyze the following batch of articles:\n\n{json.dumps(articles_data, indent=2)}"
        
        response = openai.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
        )
        
        response_text = response.choices[0].message.content
        
        try:
            analysis_data = json.loads(response_text)
        except json.JSONDecodeError:
            try:
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']') + 1

                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    analysis_data = json.loads(json_str)
                else:
                    raise ValueError("Could not extract JSON from response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing AI response: {e}")
                print(f"Raw response: {response_text}")

                return []
        
        results = []
        for item in analysis_data:
            original_article = next(
                (a for a in articles if a.title == item.get("original_title")), 
                None
            )
            
            if original_article:
                original_link = self.decode_google_news_url(item["original_link"])

                result = AnalysisResult(
                    importance_score=item["importance_score"],
                    summary=item["summary"],
                    original_title=item["original_title"],
                    original_link=original_link,
                    reasoning=item["reasoning"],
                    description=item["description"],
                )

                results.append(result)
        
        return results
    
    def generate_scout_report(self, rss_url: str) -> ScoutReport:
        """Generate a complete scout report from an RSS feed"""

        try:
            articles = self.news_fetcher.fetch_news_from_rss(rss_url)
            
            if not articles:
                raise Exception("No news articles found in the feed.")

            analysis_results = self.analyze_articles(articles)
            
            important_findings = [r for r in analysis_results if r.importance_score >= 5]
            
            report = ScoutReport(
                generated_at=datetime.now(),
                analyzed_articles=len(articles),
                important_findings=important_findings
            )
            
            return report

        except Exception as e:
            print(f"Error generating scout report: {e}")
            return

    def decode_google_news_url(self, url: str) -> str:
        """Decode a Google News URL to its original article URL."""

        try:
            decoded_result = gnewsdecoder(url, interval=1)
            
            if decoded_result.get("status"):
                return decoded_result["decoded_url"]
            else:
                print(f"Error decoding URL {url}: {decoded_result.get('message')}")

                return url 
                
        except Exception as e:
            print(f"Exception decoding URL {url}: {e}")
            
            return url
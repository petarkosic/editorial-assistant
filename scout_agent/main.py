import os
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
from agent import NewsScoutAgent

load_dotenv()

def run_scouting_task():
    """Task to run the news scouting agent"""
    print(f"[{datetime.now().isoformat()}] Starting news scouting task...")
    
    agent = NewsScoutAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
    
    # RSS feed URL (example: Google News search for "artificial intelligence")
    # rss_url = "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en"
    
    rss_url = "https://news.google.com/rss/hl=en-US&gl=US&ceid=US:en"

    try:
        report = agent.generate_scout_report(rss_url)
        
        print(f"Analyzed {report.analyzed_articles} articles")
        print(f"Found {len(report.important_findings)} important stories:")
        
        for finding in report.important_findings:
            print(f"\nScore: {finding.importance_score}/10")
            print(f"Title: {finding.original_title}")
            print(f"Summary: {finding.summary}")
            if finding.reasoning:
                print(f"Reasoning: {finding.reasoning}")
            print(f"Link: {finding.original_link}")
            print("-" * 80)
            
        with open(f"scout_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            f.write(report.json(indent=2))
            
    except Exception as e:
        print(f"Error during scouting task: {e}")

if __name__ == "__main__":
    run_scouting_task()
    
    schedule.every().hour.do(run_scouting_task)
    
    print("News scouting agent started. Press Ctrl+C to exit.")
    
    while True:
        schedule.run_pending()
        time.sleep(1)
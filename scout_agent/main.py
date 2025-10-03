import os
import sys
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
from agent import NewsScoutAgent

load_dotenv()

CATEGORIES = ["world", "business", "entertainment", "health", "science", "sports", "technology"]

def run_scouting_task(rss_url, description = ""):
    """Task to run the news scouting agent"""
    print(f"[{datetime.now().isoformat()}] Starting news scouting task...")
    
    agent = NewsScoutAgent()

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

        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)

        desc = "".join(c for c in description if c.isalnum() or c in (' ', '_')).rstrip()
        filename = f"scout_report_{desc}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = os.path.join(reports_dir, filename)

        with open(filepath, "w") as f:
            f.write(report.model_dump_json())

        print(f"\nReport saved to {filepath}")
            
    except Exception as e:
        print(f"Error during scouting task: {e}")


def get_user_choice():
    """Display menu and get user choice"""
    print("\n--- News Scouting Agent ---")
    print("Please select an option:")
    print("1) Show top stories")
    print("2) Choose a category")
    print("3) Search for specific terms")
    print("4) Exit")
    
    while True:
        choice = input("Enter your choice (1-4): ")
        
        if choice in ["1", "2", "3", "4"]:
            return choice

        print("Invalid choice. Please enter a number between 1 and 4.")


def get_category_choice():
    """Display categories and get user choice from a numbered list"""
    print("\n--- Available Categories ---")

    for i, name in enumerate(CATEGORIES, 1):
        print(f"{i}) {name}")
    
    while True:
        try:
            choice_str = input(f"Enter your choice (1-{len(CATEGORIES)}): ")
            choice_index = int(choice_str) - 1

            if 0 <= choice_index < len(CATEGORIES):
                return CATEGORIES[choice_index]
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(CATEGORIES)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def get_search_terms():
    """Get search terms from user, ensuring it's not empty"""
    while True:
        terms = input("Enter search terms: ").strip()

        if terms:
            return terms

        print("Search terms cannot be empty. Please try again.")


if __name__ == "__main__":

    choice = get_user_choice()

    if choice == '1':
        rss_url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        description = "top stories"
    elif choice == "2":
        category = get_category_choice()
        rss_url = f"https://news.google.com/rss/search?q={category}&hl=en-US&gl=US&ceid=US:en"
        description = f"Category: {category}"
    elif choice == "3":
        search_term = get_search_terms()
        format_term = search_term.replace(" ", "+")
        rss_url = f"https://news.google.com/rss/search?q={format_term}&hl=en-US&gl=US&ceid=US:en"
        description = f"Search: {search_term}"
    elif choice == "4":
        print("Exiting...")
        sys.exit(0)

    run_scouting_task(rss_url, description)

    schedule.every().hour.do(lambda: run_scouting_task, rss_url, description)

    print(f"News scouting agent started for {description}. Press Ctrl+C to exit.")
    print(f"The agent will run every hour. To stop the agent, press Ctrl+C.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nNews scouting agent stopped.")

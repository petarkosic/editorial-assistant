import os
import json
from datetime import datetime
from dotenv import load_dotenv
from evaluator import NewsScoutEvaluator
from models import ScoutReport, NewsArticle

load_dotenv()

def list_scout_reports(reports_dir: str = "reports") -> list:
    """List all available scout reports"""
    if not os.path.exists(reports_dir):
        return []
    
    reports = []
    for filename in os.listdir(reports_dir):
        if filename.startswith("scout_report_") and filename.endswith(".json"):
            filepath = os.path.join(reports_dir, filename)
            mtime = os.path.getmtime(filepath)

            reports.append({
                "filename": filename,
                "filepath": filepath,
                "modified": datetime.fromtimestamp(mtime)
            })
    
    reports.sort(key=lambda x: x["modified"], reverse=True)
    return reports

def load_scout_report(filepath: str) -> ScoutReport:
    """Load a scout report from JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    return ScoutReport(**report_data)

def evaluate_existing_report(report_filepath: str):
    """Evaluate an existing scout report"""
    
    print(f"[{datetime.now().isoformat()}] Starting evaluation of existing report...")
    print(f"Report: {os.path.basename(report_filepath)}")
    print("-" * 80)

    print("\n1. Loading Scout Report...")
    try:
        report = load_scout_report(report_filepath)
    except Exception as e:
        print(f"Error loading report: {e}")
        return
    
    print(f"   ✓ Loaded report from {report.generated_at}")
    print(f"   ✓ Report analyzed {report.analyzed_articles} articles")
    print(f"   ✓ Found {len(report.important_findings)} important stories")
    
    if not report.important_findings:
        print("\n⚠️  No important findings to evaluate in this report.")
        return
    
    print("\n2. Reconstructing Article Data...")
    articles_to_eval = []
    analyses_to_eval = []
    
    for finding in report.important_findings:
        article = NewsArticle(
            title=finding.original_title,
            link=finding.original_link,
            pub_date=None,  # Not stored in the finding
            source="Unknown",  # Not stored in the finding
            description=finding.description  # Related links
        )
        articles_to_eval.append(article)
        analyses_to_eval.append(finding)
    
    print(f"   ✓ Reconstructed {len(articles_to_eval)} articles for evaluation")
    
    print("\n3. Evaluating Analysis Quality...")
    evaluator = NewsScoutEvaluator()
    
    try:
        eval_report = evaluator.evaluate_batch(articles_to_eval, analyses_to_eval)
    except Exception as e:
        print(f"Error during evaluation: {e}")
        return
    
    evaluator.print_evaluation_report(eval_report)
    
    reports_dir = "evaluations"
    os.makedirs(reports_dir, exist_ok=True)
    
    original_filename = os.path.basename(report_filepath)
    desc_part = original_filename.replace("scout_report_", "").replace(".json", "")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    eval_filename = f"evaluation_{desc_part}_{timestamp}.json"
    eval_filepath = os.path.join(reports_dir, eval_filename)
    
    evaluator.save_evaluation_report(eval_report, eval_filepath)
    
    print("\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    print(f"Original Report: {os.path.basename(report_filepath)}")
    print(f"Generated At: {report.generated_at}")
    print(f"Evaluated Articles: {len(articles_to_eval)}")
    print(f"Average Quality Score: {eval_report.average_score:.2f}/5.0")
    
    if eval_report.average_score >= 4.5:
        print("✓ Agent performance: EXCELLENT - Keep it up!")
    elif eval_report.average_score >= 4.0:
        print("✓ Agent performance: VERY GOOD - Minor improvements possible")
    elif eval_report.average_score >= 3.5:
        print("⚠ Agent performance: GOOD - Some improvements recommended")
    elif eval_report.average_score >= 3.0:
        print("⚠ Agent performance: FAIR - Consider reviewing prompts")
    else:
        print("✗ Agent performance: POOR - Prompts need significant improvement")
    
    return eval_report

def select_report_interactively():
    """Interactive menu to select a scout report to evaluate"""
    reports = list_scout_reports()
    
    if not reports:
        print("No scout reports found in the 'reports/' directory.")
        print("Run 'uv run main.py' first to generate some reports.")
        return None
    
    print("\n" + "="*80)
    print("AVAILABLE SCOUT REPORTS")
    print("="*80)
    
    for i, report in enumerate(reports[:10], 1): 
        print(f"{i}. {report['filename']}")
        print(f"   Generated: {report['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    if len(reports) > 10:
        print(f"\n(Showing 10 most recent out of {len(reports)} total reports)")
    
    print("\nSelect a report to evaluate:")
    
    while True:
        try:
            choice = input(f"Enter number (1-{min(10, len(reports))}), or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= min(10, len(reports)):
                return reports[choice_num - 1]['filepath']
            else:
                print(f"Invalid choice. Please enter a number between 1 and {min(10, len(reports))}")
        except ValueError:
            print("Invalid input. Please enter a number or 'q'")

def evaluate_latest_report():
    """Evaluate the most recent scout report"""
    reports = list_scout_reports()
    
    if not reports:
        print("No scout reports found in the 'reports/' directory.")
        print("Run 'uv run main.py' first to generate some reports.")
        return None
    
    latest_report = reports[0]
    print(f"\nEvaluating latest report: {latest_report['filename']}")
    print(f"Generated: {latest_report['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return evaluate_existing_report(latest_report['filepath'])

def evaluate_all_recent_reports(count: int = 5):
    """Evaluate multiple recent reports and show aggregate statistics"""
    reports = list_scout_reports()[:count]
    
    if not reports:
        print("No scout reports found in the 'reports/' directory.")
        return
    
    print(f"\nEvaluating {len(reports)} most recent reports...")
    print("="*80)
    
    all_scores = []
    
    for i, report_info in enumerate(reports, 1):
        print(f"\n[{i}/{len(reports)}] Evaluating: {report_info['filename']}")
        print("-"*80)
        
        try:
            eval_report = evaluate_existing_report(report_info['filepath'])
            if eval_report:
                all_scores.append({
                    'filename': report_info['filename'],
                    'score': eval_report.average_score,
                    'generated': report_info['modified']
                })
        except Exception as e:
            print(f"Error evaluating report: {e}")
            continue
    
    if all_scores:
        print("\n" + "="*80)
        print("AGGREGATE STATISTICS")
        print("="*80)
        avg_score = sum(s['score'] for s in all_scores) / len(all_scores)
        max_score = max(all_scores, key=lambda x: x['score'])
        min_score = min(all_scores, key=lambda x: x['score'])
        
        print(f"Reports Evaluated: {len(all_scores)}")
        print(f"Average Score: {avg_score:.2f}/5.0")
        print(f"Best Score: {max_score['score']:.2f}/5.0 ({max_score['filename']})")
        print(f"Worst Score: {min_score['score']:.2f}/5.0 ({min_score['filename']})")

        if len(all_scores) >= 2:
            recent_avg = sum(s['score'] for s in all_scores[:2]) / 2
            older_avg = sum(s['score'] for s in all_scores[-2:]) / 2

            if recent_avg > older_avg:
                print(f"Trend: ↗ Improving (Recent: {recent_avg:.2f}, Older: {older_avg:.2f})")
            elif recent_avg < older_avg:
                print(f"Trend: ↘ Declining (Recent: {recent_avg:.2f}, Older: {older_avg:.2f})")
            else:
                print(f"Trend: → Stable ({recent_avg:.2f})")

if __name__ == "__main__":
    import sys
    
    print("\n--- News Scout Report Evaluator ---")
    print("Evaluate existing scout reports from the reports/ directory")
    print()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--latest":
            evaluate_latest_report()
        elif sys.argv[1] == "--file" and len(sys.argv) > 2:
            evaluate_existing_report(sys.argv[2])
        elif sys.argv[1] == "--all":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            evaluate_all_recent_reports(count)
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  uv run evaluate.py                 # Interactive menu")
            print("  uv run evaluate.py --latest        # Evaluate most recent report")
            print("  uv run evaluate.py --file <path>   # Evaluate specific report")
            print("  uv run evaluate.py --all [count]   # Evaluate N recent reports (default: 5)")
            print("  uv run evaluate.py --help          # Show this help")
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help to see available options")
    else:
        print("Select evaluation mode:")
        print("1) Choose from list of existing reports")
        print("2) Evaluate the latest report")
        print("3) Evaluate last 5 reports (batch)")
        print("4) Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            report_path = select_report_interactively()
            if report_path:
                evaluate_existing_report(report_path)
        elif choice == "2":
            evaluate_latest_report()
        elif choice == "3":
            count = input("How many recent reports to evaluate? (default: 5): ").strip()
            count = int(count) if count.isdigit() else 5
            evaluate_all_recent_reports(count)
        elif choice == "4":
            print("Exiting...")
        else:
            print("Invalid choice.")
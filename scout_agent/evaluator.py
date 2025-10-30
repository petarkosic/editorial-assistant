import os
import openai
import json
from typing import List, Dict
from datetime import datetime
from models import AnalysisResult, NewsArticle
from pydantic import BaseModel, Field

class EvaluationScore(BaseModel):
    """Individual evaluation score for one criterion"""
    criterion: str
    score: int = Field(..., ge=1, le=5, description="Score from 1-5")
    reasoning: str
    
class ArticleEvaluation(BaseModel):
    """Complete evaluation for a single article analysis"""
    article_title: str
    overall_score: float = Field(..., ge=1, le=5)
    scores: List[EvaluationScore]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: str

class EvaluationReport(BaseModel):
    """Complete evaluation report for a batch of analyses"""
    evaluated_at: datetime
    total_articles: int
    average_score: float
    evaluations: List[ArticleEvaluation]
    overall_feedback: str

class NewsScoutEvaluator:
    """LLM-as-a-Judge evaluator for News Scout Agent outputs"""
    
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        openai.base_url = os.getenv("OPENAI_API_BASE_URL")
        
    def evaluate_analysis(
        self, 
        article: NewsArticle, 
        analysis: AnalysisResult
    ) -> ArticleEvaluation:
        """Evaluate a single article analysis using LLM as judge"""
        
        system_prompt = """You are an expert evaluator assessing the quality of news article analysis performed by an AI assistant editor.

            Your task is to evaluate how well the AI analyzed a news article based on these criteria:

            1. **Importance Score Accuracy (1-5)**: Is the importance score (1-10) appropriate for this article? Consider impact, novelty, and public interest.

            2. **Summary Quality (1-5)**: Is the one-sentence summary clear, concise, and captures the story's significance?

            3. **Reasoning Clarity (1-5)**: Is the reasoning behind the score logical, specific, and well-justified?

            4. **Consistency (1-5)**: Does the importance score align with the summary and reasoning provided?

            5. **Relevance (1-5)**: Did the AI correctly identify whether this is truly important news (score ≥5) or should be filtered out?

            For each criterion, provide:
            - A score from 1-5 (5 = excellent, 1 = poor)
            - Brief reasoning for the score

            Also provide:
            - Overall score (average of all criteria)
            - 2-3 key strengths
            - 2-3 key weaknesses
            - Actionable suggestions for improvement

            Return your evaluation as valid JSON in this format:
            {
            "article_title": "original article title",
            "overall_score": 4.2,
            "scores": [
                {
                "criterion": "Importance Score Accuracy",
                "score": 4,
                "reasoning": "explanation here"
                }
            ],
            "strengths": ["strength 1", "strength 2"],
            "weaknesses": ["weakness 1", "weakness 2"],
            "suggestions": "specific suggestions for improvement"
            }
            """
        
        user_prompt = f"""Please evaluate this article analysis:

            ORIGINAL ARTICLE:
            Title: {article.title}
            Source: {article.source}
            Published: {article.pub_date}
            Related Links: {len(article.description) if article.description else 0} similar articles

            AI ANALYSIS:
            Importance Score: {analysis.importance_score}/10
            Summary: {analysis.summary}
            Reasoning: {analysis.reasoning}

            Evaluate the quality of this analysis based on the criteria provided."""

        response = openai.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
        )
        
        response_text = response.choices[0].message.content
        
        try:
            eval_data = json.loads(response_text)
        except json.JSONDecodeError:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                eval_data = json.loads(json_str)
            else:
                raise ValueError("Could not extract JSON from evaluation response")
        
        return ArticleEvaluation(**eval_data)
    
    def evaluate_batch(
        self, 
        articles: List[NewsArticle], 
        analyses: List[AnalysisResult]
    ) -> EvaluationReport:
        """Evaluate a batch of article analyses"""
        
        if len(articles) != len(analyses):
            raise ValueError("Number of articles must match number of analyses")
        
        evaluations = []
        total_score = 0
        
        for article, analysis in zip(articles, analyses):
            eval_result = self.evaluate_analysis(article, analysis)
            evaluations.append(eval_result)
            total_score += eval_result.overall_score
        
        avg_score = total_score / len(evaluations) if evaluations else 0
        
        overall_feedback = self._generate_overall_feedback(evaluations, avg_score)
        
        return EvaluationReport(
            evaluated_at=datetime.now(),
            total_articles=len(articles),
            average_score=round(avg_score, 2),
            evaluations=evaluations,
            overall_feedback=overall_feedback
        )
    
    def _generate_overall_feedback(
        self, 
        evaluations: List[ArticleEvaluation], 
        avg_score: float
    ) -> str:
        """Generate overall feedback summary"""
        
        if avg_score >= 4.5:
            performance = "excellent"
        elif avg_score >= 4.0:
            performance = "very good"
        elif avg_score >= 3.5:
            performance = "good"
        elif avg_score >= 3.0:
            performance = "satisfactory"
        else:
            performance = "needs improvement"


        all_strengths = []
        all_weaknesses = []
        
        for eval in evaluations:
            all_strengths.extend(eval.strengths)
            all_weaknesses.extend(eval.weaknesses)
        
        feedback = f"Overall Performance: {performance.title()} (Average Score: {avg_score:.2f}/5.0)\n\n"
        
        if all_strengths:
            feedback += "Common Strengths:\n"

            for strength in set(all_strengths[:5]):
                feedback += f"  - {strength}\n"
        
        if all_weaknesses:
            feedback += "\nAreas for Improvement:\n"
            for weakness in set(all_weaknesses[:5]):
                feedback += f"  - {weakness}\n"
        
        return feedback
    
    def save_evaluation_report(self, report: EvaluationReport, filepath: str):
        """Save evaluation report to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report.model_dump_json(indent=2))
        print(f"Evaluation report saved to {filepath}")
    
    def print_evaluation_report(self, report: EvaluationReport):
        """Print evaluation report to console"""
        print("\n" + "="*80)
        print("EVALUATION REPORT")
        print("="*80)
        print(f"Evaluated at: {report.evaluated_at}")
        print(f"Total Articles Evaluated: {report.total_articles}")
        print(f"Average Score: {report.average_score:.2f}/5.0")
        print("\n" + report.overall_feedback)
        
        print("\nDETAILED EVALUATIONS:")
        print("-"*80)
        
        for i, eval in enumerate(report.evaluations, 1):
            print(f"\n{i}. {eval.article_title}")
            print(f"   Overall Score: {eval.overall_score:.1f}/5.0")
            
            print("\n   Criterion Scores:")
            for score in eval.scores:
                print(f"   - {score.criterion}: {score.score}/5")
                print(f"     {score.reasoning}")
            
            if eval.strengths:
                print("\n   Strengths:")
                for strength in eval.strengths:
                    print(f"   ✓ {strength}")
            
            if eval.weaknesses:
                print("\n   Weaknesses:")
                for weakness in eval.weaknesses:
                    print(f"   ✗ {weakness}")
            
            if eval.suggestions:
                print(f"\n   Suggestions: {eval.suggestions}")
            
            print("-"*80)
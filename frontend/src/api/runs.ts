import { api } from './client';

export interface ScoutFinding {
	importance_score: number;
	summary: string;
	original_title: string;
	original_link: string;
	reasoning?: string | null;
	[k: string]: unknown;
}

export interface ScoutReportContent {
	generated_at: string;
	analyzed_articles: number;
	important_findings: ScoutFinding[];
}

export interface StoryOut {
	id: string;
	status: string;
	selected: boolean;
	finding: ScoutFinding;
}

export interface EvaluationScoreOut {
	criterion: string;
	score: number;
	reasoning: string;
}

export interface EvaluationOut {
	stage: string;
	overall_score: number;
	scores: EvaluationScoreOut[];
	strengths: string[];
	weaknesses: string[];
	suggestions: string;
}

export interface RunSummary {
	id: string;
	status: string;
	source_kind: string;
	source_query: string | null;
	error: string | null;
	created_at: string;
	story_count: number;
}

export interface RunDetail {
	id: string;
	status: string;
	source_kind: string;
	source_query: string | null;
	error: string | null;
	created_at: string;
	stories: StoryOut[];
	scout_report: ScoutReportContent | null;
	scout_evaluation: EvaluationOut | null;
}

export interface CreateRunBody {
	source_kind: 'top_stories' | 'category' | 'search';
	source_query: string | null;
}

export function createRun(body: CreateRunBody): Promise<RunSummary> {
	return api.post<RunSummary>('/runs', body);
}

export function listRuns(): Promise<RunSummary[]> {
	return api.get<RunSummary[]>('/runs');
}

export function getRun(id: string): Promise<RunDetail> {
	return api.get<RunDetail>(`/runs/${id}`);
}

export function deleteRun(id: string): Promise<void> {
	return api.delete<void>(`/runs/${id}`);
}

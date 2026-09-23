import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
	approveStory,
	createRun,
	deleteRun,
	getRun,
	getStory,
	listRuns,
	reevaluateStory,
	rejectStory,
	retryStory,
	selectStories,
	type RunDetail,
	type StoryDetail,
} from '../api/runs';

export const runKeys = {
	all: ['runs'] as const,
	detail: (id: string) => ['runs', id] as const,
	story: (runId: string, storyId: string) =>
		['runs', runId, 'stories', storyId] as const,
};

// Poll while something is actually working server-side: the scout stage, or
// at least one story mid-research/mid-synthesis. `run.status === 'in_progress'`
// alone isn't enough — a run stays 'in_progress' from the moment you select
// stories until every one of them is approved/rejected, including the whole
// stretch where a story is just sitting at 'research_ready' waiting on you.
export function pollWhileActive(
	run: Pick<RunDetail, 'status' | 'stories'> | undefined,
): number | false {
	if (!run) return false;
	if (run.status === 'scouting') return 2000;

	const anyStoryActive = run.stories.some(
		(s) => s.status === 'researching' || s.status === 'synthesizing',
	);

	return anyStoryActive ? 2000 : false;
}

export function useRuns() {
	return useQuery({ queryKey: runKeys.all, queryFn: listRuns });
}

export function useRun(id: string | undefined) {
	return useQuery({
		queryKey: runKeys.detail(id ?? ''),
		queryFn: () => getRun(id as string),
		enabled: Boolean(id),
		refetchInterval: (query) =>
			pollWhileActive(query.state.data as RunDetail | undefined),
	});
}

export function useCreateRun() {
	const qc = useQueryClient();
	return useMutation({
		mutationFn: createRun,
		onSuccess: () => qc.invalidateQueries({ queryKey: runKeys.all }),
	});
}

export function useDeleteRun() {
	const qc = useQueryClient();
	return useMutation({
		mutationFn: deleteRun,
		onSuccess: () => qc.invalidateQueries({ queryKey: runKeys.all }),
	});
}

function pollWhileStoryActive(status: string | undefined): number | false {
	return status === 'researching' || status === 'synthesizing' ? 2000 : false;
}

export function useStory(runId: string, storyId: string) {
	return useQuery({
		queryKey: runKeys.story(runId, storyId),
		queryFn: () => getStory(runId, storyId),
		refetchInterval: (query) =>
			pollWhileStoryActive(
				(query.state.data as StoryDetail | undefined)?.status,
			),
	});
}

export function useSelectStories(runId: string) {
	const qc = useQueryClient();
	return useMutation({
		mutationFn: (storyIds: string[]) => selectStories(runId, storyIds),
		onSuccess: () => qc.invalidateQueries({ queryKey: runKeys.detail(runId) }),
	});
}

function useStoryAction(
	runId: string,
	storyId: string,
	fn: (runId: string, storyId: string) => Promise<StoryDetail>,
) {
	const qc = useQueryClient();
	return useMutation({
		mutationFn: () => fn(runId, storyId),
		onSuccess: () => {
			qc.invalidateQueries({ queryKey: runKeys.detail(runId) });
			qc.invalidateQueries({ queryKey: runKeys.story(runId, storyId) });
		},
	});
}

export function useApproveStory(runId: string, storyId: string) {
	return useStoryAction(runId, storyId, approveStory);
}

export function useRejectStory(runId: string, storyId: string) {
	return useStoryAction(runId, storyId, rejectStory);
}

export function useRetryStory(runId: string, storyId: string) {
	return useStoryAction(runId, storyId, retryStory);
}

export function useReevaluateStory(runId: string, storyId: string) {
	return useStoryAction(runId, storyId, reevaluateStory);
}

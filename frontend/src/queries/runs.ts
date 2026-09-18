import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createRun, deleteRun, getRun, listRuns, type RunDetail } from '../api/runs';

export const runKeys = {
  all: ['runs'] as const,
  detail: (id: string) => ['runs', id] as const,
};

export function pollWhileActive(status: string | undefined): number | false {
  return status === 'scouting' || status === 'in_progress' ? 2000 : false;
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
      pollWhileActive((query.state.data as RunDetail | undefined)?.status),
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

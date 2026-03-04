const BASE = '';

export interface HealthResponse {
  status: string;
  provider: string;
  model: string;
  version: string;
}

export interface OptimizationOptions {
  strategy?: string;
  model?: string;
  context_files?: string[];
  github_repo?: string;
}

export interface HistoryParams {
  page?: number;
  page_size?: number;
  search?: string;
  strategy?: string;
  sort_by?: string;
  sort_dir?: string;
}

export interface HistoryResponse {
  items: Array<Record<string, unknown>>;
  total: number;
  page: number;
  page_size: number;
}

export interface OptimizationResponse {
  id: string;
  original_prompt: string;
  optimized_prompt: string;
  overall_score: number;
  strategy: string;
  model: string;
  created_at: string;
  stages: Record<string, unknown>;
}

// ---- Health ----

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE}/api/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

// ---- SSE Optimization Stream ----

export interface SSEEvent {
  event: string;
  data: unknown;
}

export type SSECallback = (event: SSEEvent) => void;

export async function startOptimization(
  prompt: string,
  options: OptimizationOptions,
  onEvent: SSECallback,
  onError: (err: Error) => void,
  onComplete: () => void
): Promise<AbortController> {
  const controller = new AbortController();

  try {
    const res = await fetch(`${BASE}/api/optimize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, ...options }),
      signal: controller.signal
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`Optimization failed (${res.status}): ${errorText}`);
    }

    if (!res.body) {
      throw new Error('No response body for SSE stream');
    }

    // Parse SSE from ReadableStream
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    const processStream = async () => {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          let currentEvent = 'message';
          let currentData = '';

          for (const line of lines) {
            if (line.startsWith('event: ')) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              currentData = line.slice(6);
            } else if (line === '' && currentData) {
              // End of event
              try {
                const parsed = JSON.parse(currentData);
                onEvent({ event: currentEvent, data: parsed });
              } catch {
                onEvent({ event: currentEvent, data: currentData });
              }
              currentEvent = 'message';
              currentData = '';
            }
          }
        }
        onComplete();
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          onError(err as Error);
        }
      }
    };

    processStream();
  } catch (err) {
    if ((err as Error).name !== 'AbortError') {
      onError(err as Error);
    }
  }

  return controller;
}

// ---- History ----

export async function fetchHistory(params: HistoryParams = {}): Promise<HistoryResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.search) searchParams.set('search', params.search);
  if (params.strategy) searchParams.set('strategy', params.strategy);
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.sort_dir) searchParams.set('sort_dir', params.sort_dir);

  const res = await fetch(`${BASE}/api/history?${searchParams.toString()}`);
  if (!res.ok) throw new Error(`Fetch history failed: ${res.status}`);
  return res.json();
}

export async function fetchOptimization(id: string): Promise<OptimizationResponse> {
  const res = await fetch(`${BASE}/api/history/${id}`);
  if (!res.ok) throw new Error(`Fetch optimization failed: ${res.status}`);
  return res.json();
}

export async function deleteOptimization(id: string): Promise<void> {
  const res = await fetch(`${BASE}/api/history/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Delete optimization failed: ${res.status}`);
}

export async function patchOptimization(id: string, data: Record<string, unknown>): Promise<OptimizationResponse> {
  const res = await fetch(`${BASE}/api/history/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error(`Patch optimization failed: ${res.status}`);
  return res.json();
}

// ---- GitHub Auth ----

export async function connectGitHub(pat: string): Promise<{ username: string; repos: Array<Record<string, unknown>> }> {
  const res = await fetch(`${BASE}/auth/github/connect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pat })
  });
  if (!res.ok) throw new Error(`GitHub connect failed: ${res.status}`);
  return res.json();
}

export async function disconnectGitHub(): Promise<void> {
  const res = await fetch(`${BASE}/auth/github/disconnect`, { method: 'POST' });
  if (!res.ok) throw new Error(`GitHub disconnect failed: ${res.status}`);
}

export async function fetchGitHubRepos(): Promise<Array<Record<string, unknown>>> {
  const res = await fetch(`${BASE}/auth/github/repos`);
  if (!res.ok) throw new Error(`Fetch repos failed: ${res.status}`);
  return res.json();
}

export async function fetchGitHubFiles(repo: string, path: string = ''): Promise<Array<Record<string, unknown>>> {
  const params = new URLSearchParams({ repo, path });
  const res = await fetch(`${BASE}/auth/github/files?${params.toString()}`);
  if (!res.ok) throw new Error(`Fetch files failed: ${res.status}`);
  return res.json();
}

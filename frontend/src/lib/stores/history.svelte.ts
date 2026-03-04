export interface HistoryEntry {
  id: string;
  raw_prompt: string;
  optimized_prompt?: string;
  overall_score?: number;
  strategy?: string;
  model?: string;
  created_at: string;
  duration_ms?: number;
  tags?: string[];
}

export interface HistoryFilters {
  search: string;
  strategy: string | null;
  sortBy: 'created_at' | 'overall_score';
  sortDir: 'asc' | 'desc';
  page: number;
  pageSize: number;
}

class HistoryStore {
  entries = $state<HistoryEntry[]>([]);
  totalCount = $state(0);
  isLoading = $state(false);
  selectedId = $state<string | null>(null);
  filters = $state<HistoryFilters>({
    search: '',
    strategy: null,
    sortBy: 'created_at',
    sortDir: 'desc',
    page: 1,
    pageSize: 20
  });

  get selectedEntry(): HistoryEntry | undefined {
    return this.entries.find(e => e.id === this.selectedId);
  }

  get hasMore(): boolean {
    return this.entries.length < this.totalCount;
  }

  setEntries(entries: HistoryEntry[], total: number) {
    this.entries = entries;
    this.totalCount = total;
  }

  appendEntries(entries: HistoryEntry[], total: number) {
    this.entries = [...this.entries, ...entries];
    this.totalCount = total;
  }

  removeEntry(id: string) {
    this.entries = this.entries.filter(e => e.id !== id);
    this.totalCount--;
    if (this.selectedId === id) {
      this.selectedId = null;
    }
  }

  select(id: string) {
    this.selectedId = id;
  }
}

export const history = new HistoryStore();

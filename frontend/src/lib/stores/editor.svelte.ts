export type SubTab = 'edit' | 'pipeline' | 'history';

export interface EditorTab {
  id: string;
  label: string;
  type: 'prompt' | 'artifact' | 'chain' | 'strategy-ref';
  promptText?: string;
  dirty?: boolean;
  optimizationId?: string;
  strategy?: string;
}

const MAX_TABS = 8;
const TAB_STORAGE_KEY = 'pf_editorTabs';

interface PersistedTabState {
  tabs: Array<{ id: string; label: string; type: string; optimizationId?: string; strategy?: string }>;
  activeTabId: string | null;
}

class EditorStore {
  openTabs = $state<EditorTab[]>([]);
  private _activeTabId = $state<string | null>(null);
  activeSubTab = $state<SubTab>('edit');
  private _lastAccessed = new Map<string, number>();

  get activeTabId(): string | null { return this._activeTabId; }
  set activeTabId(id: string | null) {
    this._activeTabId = id;
    if (id) this._lastAccessed.set(id, Date.now());
    this._persistTabs();
  }

  get activeTab(): EditorTab | undefined {
    return this.openTabs.find(t => t.id === this.activeTabId);
  }

  openTab(tab: EditorTab) {
    const existing = this.openTabs.find(t => t.id === tab.id);
    if (existing) {
      this.activeTabId = tab.id;
      return;
    }
    if (this.openTabs.length >= MAX_TABS) {
      let oldestId = '';
      let oldestTime = Infinity;
      for (const t of this.openTabs) {
        if (t.id === this.activeTabId) continue;
        const tTime = this._lastAccessed.get(t.id) ?? 0;
        if (tTime < oldestTime) { oldestTime = tTime; oldestId = t.id; }
      }
      if (oldestId) {
        this.openTabs.splice(this.openTabs.findIndex(t => t.id === oldestId), 1);
        this._lastAccessed.delete(oldestId);
      }
    }
    this.openTabs.push(tab);
    this._lastAccessed.set(tab.id, Date.now());
    this._activeTabId = tab.id;
    this._persistTabs();
  }

  closeTab(id: string) {
    const idx = this.openTabs.findIndex(t => t.id === id);
    if (idx === -1) return;
    this.openTabs.splice(idx, 1);
    this._lastAccessed.delete(id);
    if (this.activeTabId === id) {
      this._activeTabId = this.openTabs.length > 0
        ? this.openTabs[Math.min(idx, this.openTabs.length - 1)].id
        : null;
    }
    this._persistTabs();
  }

  moveTab(fromIndex: number, toIndex: number) {
    if (fromIndex === toIndex || fromIndex < 0 || toIndex < 0) return;
    if (fromIndex >= this.openTabs.length || toIndex >= this.openTabs.length) return;
    const [tab] = this.openTabs.splice(fromIndex, 1);
    this.openTabs.splice(toIndex, 0, tab);
    this._persistTabs();
  }

  setSubTab(sub: SubTab) {
    this.activeSubTab = sub;
  }

  updateTabPrompt(id: string, text: string) {
    const tab = this.openTabs.find(t => t.id === id);
    if (tab) {
      tab.promptText = text;
      tab.dirty = true;
    }
  }

  saveActiveTab() {
    const tab = this.activeTab;
    if (tab) {
      tab.dirty = false;
    }
  }

  ensureWelcomeTab() {
    if (this.openTabs.length === 0) {
      this.openTab({
        id: 'welcome',
        label: 'Welcome',
        type: 'prompt',
        promptText: '',
        dirty: false
      });
    }
  }

  /** Restore tabs from localStorage. Returns true if tabs were restored. */
  loadPersistedTabs(): boolean {
    if (typeof window === 'undefined') return false;
    try {
      const raw = localStorage.getItem(TAB_STORAGE_KEY);
      if (!raw) return false;
      const state: PersistedTabState = JSON.parse(raw);
      if (!Array.isArray(state.tabs) || state.tabs.length === 0) return false;
      this.openTabs = state.tabs.map(t => ({
        id: t.id,
        label: t.label,
        type: t.type as EditorTab['type'],
        dirty: false,
        promptText: '',
        optimizationId: t.optimizationId,
        strategy: t.strategy,
      }));
      this._activeTabId = state.activeTabId;
      // Populate LRU with sequential timestamps to preserve order
      const now = Date.now();
      this.openTabs.forEach((t, i) => {
        this._lastAccessed.set(t.id, now - (this.openTabs.length - i));
      });
      return true;
    } catch {
      return false;
    }
  }

  /** Persist tab metadata to localStorage (excludes promptText). */
  private _persistTabs() {
    if (typeof window === 'undefined') return;
    const state: PersistedTabState = {
      tabs: this.openTabs.map(t => ({
        id: t.id, label: t.label, type: t.type,
        optimizationId: t.optimizationId, strategy: t.strategy,
      })),
      activeTabId: this._activeTabId,
    };
    try { localStorage.setItem(TAB_STORAGE_KEY, JSON.stringify(state)); } catch {}
  }
}

export const editor = new EditorStore();

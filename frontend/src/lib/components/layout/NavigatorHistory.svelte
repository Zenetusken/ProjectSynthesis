<script lang="ts">
  import { history } from '$lib/stores/history.svelte';
  import { editor } from '$lib/stores/editor.svelte';
  import { fetchHistory } from '$lib/api/client';
  import ScoreCircle from '$lib/components/shared/ScoreCircle.svelte';
  import { onMount } from 'svelte';

  let loading = $state(false);

  async function loadHistory() {
    loading = true;
    try {
      const res = await fetchHistory({
        page: history.filters.page,
        per_page: history.filters.pageSize,
        search: history.filters.search || undefined,
        task_type: history.filters.strategy || undefined,
        sort: history.filters.sortBy,
        order: history.filters.sortDir
      });
      history.setEntries(
        res.items.map((item: Record<string, unknown>) => ({
          id: item.id as string,
          raw_prompt: (item.raw_prompt || '') as string,
          optimized_prompt: item.optimized_prompt as string | undefined,
          overall_score: item.overall_score as number | undefined,
          strategy: (item.primary_framework || item.strategy) as string | undefined,
          model: (item.provider_used || item.model) as string | undefined,
          created_at: item.created_at as string,
          duration_ms: item.duration_ms as number | undefined,
          tags: item.tags as string[] | undefined
        })),
        res.total
      );
    } catch {
      // API not available yet
    } finally {
      loading = false;
    }
  }

  function openHistoryEntry(entry: typeof history.entries[0]) {
    history.select(entry.id);
    editor.openTab({
      id: `history-${entry.id}`,
      label: entry.raw_prompt.slice(0, 30) + (entry.raw_prompt.length > 30 ? '...' : ''),
      type: 'prompt',
      promptText: entry.optimized_prompt || entry.raw_prompt,
      dirty: false
    });
  }

  onMount(() => {
    loadHistory();
  });
</script>

<div class="flex flex-col h-full">
  <!-- Search -->
  <div class="p-2 border-b border-border-subtle">
    <input
      type="text"
      placeholder="Search history..."
      class="w-full bg-bg-input border border-border-subtle rounded px-2 py-1 text-xs text-text-primary placeholder:text-text-dim focus:outline-none focus:border-neon-cyan/30"
      oninput={(e) => { history.filters.search = (e.target as HTMLInputElement).value; }}
    />
  </div>

  <!-- List -->
  <div class="flex-1 overflow-y-auto p-1">
    {#if loading}
      <div class="flex items-center justify-center py-8">
        <div class="w-4 h-4 border-2 border-neon-cyan/30 border-t-neon-cyan rounded-full animate-spin"></div>
      </div>
    {:else if history.entries.length === 0}
      <p class="text-xs text-text-dim px-2 py-8 text-center">No history entries yet. Forge a prompt to get started.</p>
    {:else}
      {#each history.entries as entry (entry.id)}
        <button
          class="w-full text-left px-2 py-2 rounded text-xs transition-colors mb-0.5
            {history.selectedId === entry.id
              ? 'bg-bg-hover border border-border-accent'
              : 'hover:bg-bg-hover border border-transparent'}"
          onclick={() => openHistoryEntry(entry)}
        >
          <div class="flex items-start gap-2">
            {#if entry.overall_score != null}
              <ScoreCircle score={entry.overall_score} size={20} />
            {/if}
            <div class="flex-1 min-w-0">
              <p class="text-text-primary truncate">{entry.raw_prompt.slice(0, 50)}</p>
              <div class="flex items-center gap-2 mt-0.5">
                {#if entry.strategy}
                  <span class="text-[10px] text-neon-purple">{entry.strategy}</span>
                {/if}
                <span class="text-[10px] text-text-dim">{new Date(entry.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </button>
      {/each}
    {/if}
  </div>

  <!-- Footer -->
  <div class="p-2 border-t border-border-subtle">
    <button
      class="w-full text-xs text-text-dim hover:text-neon-cyan transition-colors py-1"
      onclick={loadHistory}
    >
      Refresh
    </button>
  </div>
</div>

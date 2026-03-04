<script lang="ts">
  import { history } from '$lib/stores/history.svelte';
  import ScoreCircle from '$lib/components/shared/ScoreCircle.svelte';
  import { formatRelativeTime } from '$lib/utils/format';
</script>

<div class="p-4 space-y-3 animate-fade-in">
  <h3 class="text-xs font-semibold text-text-secondary uppercase tracking-wider">Optimization History</h3>

  {#if history.entries.length === 0}
    <div class="text-center py-12">
      <p class="text-sm text-text-dim">No optimization history for this prompt.</p>
    </div>
  {:else}
    {#each history.entries as entry (entry.id)}
      <div class="bg-bg-card border border-border-subtle rounded-lg p-3 animate-stagger-fade-in hover:border-border-accent transition-colors">
        <div class="flex items-start gap-3">
          {#if entry.overall_score != null}
            <ScoreCircle score={entry.overall_score} size={32} />
          {/if}
          <div class="flex-1 min-w-0">
            <p class="text-sm text-text-primary line-clamp-2">{entry.original_prompt.slice(0, 100)}</p>
            <div class="flex items-center gap-2 mt-1.5">
              {#if entry.strategy}
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-neon-purple/10 text-neon-purple border border-neon-purple/20">
                  {entry.strategy}
                </span>
              {/if}
              <span class="text-[10px] text-text-dim">{formatRelativeTime(entry.created_at)}</span>
              {#if entry.duration_ms}
                <span class="text-[10px] text-text-dim">{(entry.duration_ms / 1000).toFixed(1)}s</span>
              {/if}
            </div>
          </div>
        </div>
      </div>
    {/each}
  {/if}
</div>

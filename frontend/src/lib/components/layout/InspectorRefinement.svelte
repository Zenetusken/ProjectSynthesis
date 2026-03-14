<script lang="ts">
  import { refinement } from '$lib/stores/refinement.svelte';

  // Derive a flat reverse-chronological list of turns from all branches
  let allTurns = $derived.by(() => {
    const turns: Array<{
      branchLabel: string;
      turn: number;
      source: 'user' | 'auto';
      summary: string;
    }> = [];
    for (const branch of refinement.branches) {
      for (let i = branch.turnCount; i >= 1; i--) {
        turns.push({
          branchLabel: branch.label,
          turn: i,
          source: i % 2 === 0 ? 'auto' : 'user',
          summary: `Turn ${i} on branch "${branch.label}"`,
        });
      }
    }
    // Sort descending by turn number
    turns.sort((a, b) => b.turn - a.turn);
    return turns.slice(0, 20);
  });

  let sessionState = $derived.by(() => {
    if (refinement.refinementStreaming) return 'active';
    // No turns yet — show idle, not exhausted
    const hasTurns = refinement.branches.some((b) => b.turnCount > 0);
    if (!hasTurns) return 'idle';
    if (refinement.branches.some((b) => b.status === 'selected')) return 'compacted';
    return 'exhausted';
  });

  const SESSION_STATE_LABELS: Record<string, string> = {
    active: 'Active',
    idle: 'Idle',
    compacted: 'Compacted',
    exhausted: 'Exhausted',
  };

  const SESSION_STATE_COLORS: Record<string, string> = {
    active: 'border-neon-cyan text-neon-cyan',
    idle: 'border-text-dim/50 text-text-dim/50',
    compacted: 'border-neon-indigo text-neon-indigo',
    exhausted: 'border-text-dim text-text-dim',
  };
</script>

<div class="space-y-1.5">
  <div class="flex items-center justify-between">
    <h3 class="section-heading">Refinement</h3>
    <span
      class="border text-[8px] font-mono uppercase px-1 py-px {SESSION_STATE_COLORS[sessionState] ?? 'border-text-dim text-text-dim'}"
    >{SESSION_STATE_LABELS[sessionState] ?? sessionState}</span>
  </div>

  {#if allTurns.length === 0}
    <p class="text-[10px] text-text-dim">No refinement turns yet.</p>
  {:else}
    <div class="space-y-1.5">
      {#each allTurns as item}
        <div class="flex gap-2 p-1.5 bg-bg-card border border-border-subtle">
          <span
            class="shrink-0 border text-[9px] font-mono uppercase px-1 py-0.5 h-fit {item.source === 'user'
              ? 'border-neon-cyan text-neon-cyan'
              : 'text-neon-indigo border-neon-indigo'}"
          >{item.source === 'user' ? 'USR' : 'AUTO'}</span>
          <p class="text-[10px] text-text-secondary leading-snug line-clamp-2 break-words min-w-0">
            {item.summary}
          </p>
        </div>
      {/each}
    </div>
  {/if}
</div>

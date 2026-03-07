<script lang="ts">
  import { forge } from '$lib/stores/forge.svelte';
  import ScoreCircle from '$lib/components/shared/ScoreCircle.svelte';

  function fmtDuration(ms: number | null): string {
    if (ms == null) return '—';
    return `${(ms / 1000).toFixed(1)}s`;
  }

  function fmtScore(score: number | null): string {
    if (score == null) return '—/10';
    return `${score.toFixed(1)}/10`;
  }

  function fmtTokens(n: number | null): string {
    if (n == null) return '— tok';
    return `${n.toLocaleString()} tok`;
  }

  const summary = $derived(
    [
      `Run ${forge.completedStages} of ${forge.visibleStages.length}`,
      fmtDuration(forge.totalDuration),
      fmtScore(forge.overallScore),
      fmtTokens(forge.totalTokens),
    ].join('  ·  ')
  );
</script>

<div class="flex items-center justify-between px-1 py-0.5">
  <!-- Left: score indicator + single-line run summary -->
  <div class="flex items-center gap-2 min-w-0">
    {#if forge.overallScore != null}
      <ScoreCircle score={forge.overallScore} size={28} />
    {:else if forge.isForging}
      <div
        class="w-7 h-7 rounded-full shrink-0 animate-spin"
        style="border: 1px solid rgba(0,229,255,0.25); border-top-color: #00e5ff;"
      ></div>
    {/if}

    <span class="font-mono text-[10px] text-text-secondary leading-none truncate">
      {summary}
    </span>
  </div>

  <!-- Right: per-stage status dots -->
  <div class="flex items-center gap-1 shrink-0 ml-2">
    {#each forge.stages.filter(s => !(s === 'explore' && forge.stageStatuses[s] === 'idle')) as stage}
      {@const st = forge.stageStatuses[stage]}
      <div
        class="w-1.5 h-1.5 rounded-full transition-colors {
          st === 'done'      ? 'bg-neon-green' :
          st === 'running'   ? 'bg-neon-cyan animate-status-pulse' :
          st === 'error'     ? 'bg-neon-red' :
          st === 'timed_out' ? 'bg-neon-orange' :
          st === 'cancelled' ? 'bg-text-dim/40' :
                               'bg-text-dim/20'
        }"
        title={stage}
      ></div>
    {/each}
  </div>
</div>

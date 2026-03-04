<script lang="ts">
  import { forge } from '$lib/stores/forge.svelte';
  import ScoreBar from '$lib/components/shared/ScoreBar.svelte';

  let result = $derived(forge.stageResults['analyze']);
  let data = $derived((result?.data || {}) as Record<string, unknown>);
  let weaknesses = $derived(((data.weaknesses || []) as string[]));
  let strengths = $derived(((data.strengths || []) as string[]));
</script>

<div class="space-y-2 text-xs">
  {#if forge.stageStatuses['analyze'] === 'running'}
    <div class="flex items-center gap-2 text-neon-cyan">
      <div class="w-3 h-3 border border-neon-cyan/30 border-t-neon-cyan rounded-full animate-spin"></div>
      <span>Analyzing prompt quality...</span>
    </div>
  {:else if result}
    <!-- Scores -->
    {#if data.clarity != null}
      <div class="space-y-1">
        <div class="flex justify-between">
          <span class="text-text-dim">Clarity</span>
          <span class="text-text-secondary">{data.clarity}/10</span>
        </div>
        <ScoreBar score={data.clarity as number} max={10} />
      </div>
    {/if}
    {#if data.specificity != null}
      <div class="space-y-1">
        <div class="flex justify-between">
          <span class="text-text-dim">Specificity</span>
          <span class="text-text-secondary">{data.specificity}/10</span>
        </div>
        <ScoreBar score={data.specificity as number} max={10} />
      </div>
    {/if}

    <!-- Strengths -->
    {#if strengths.length > 0}
      <div class="mt-2">
        <span class="text-neon-green text-[10px] uppercase tracking-wider font-semibold">Strengths</span>
        <ul class="mt-1 space-y-0.5">
          {#each strengths as s}
            <li class="text-text-secondary flex gap-1.5">
              <span class="text-neon-green shrink-0">+</span>
              <span>{s}</span>
            </li>
          {/each}
        </ul>
      </div>
    {/if}

    <!-- Weaknesses -->
    {#if weaknesses.length > 0}
      <div class="mt-2">
        <span class="text-neon-red text-[10px] uppercase tracking-wider font-semibold">Weaknesses</span>
        <ul class="mt-1 space-y-0.5">
          {#each weaknesses as w}
            <li class="text-text-secondary flex gap-1.5">
              <span class="text-neon-red shrink-0">-</span>
              <span>{w}</span>
            </li>
          {/each}
        </ul>
      </div>
    {/if}
  {:else}
    <p class="text-text-dim">Waiting for Explore stage...</p>
  {/if}
</div>

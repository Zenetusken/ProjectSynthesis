<script lang="ts">
  import { forge } from '$lib/stores/forge.svelte';
  import StrategyBadge from '$lib/components/shared/StrategyBadge.svelte';

  let result = $derived(forge.stageResults['strategize']);
  let data = $derived((result?.data || {}) as Record<string, unknown>);
</script>

<div class="space-y-2 text-xs">
  {#if forge.stageStatuses['strategize'] === 'running'}
    <div class="flex items-center gap-2 text-neon-cyan">
      <div class="w-3 h-3 border border-neon-cyan/30 border-t-neon-cyan rounded-full animate-spin"></div>
      <span>Selecting optimization strategy...</span>
    </div>
  {:else if result}
    {#if data.strategy}
      <div class="flex items-center gap-2">
        <span class="text-text-dim">Selected:</span>
        <StrategyBadge strategy={data.strategy as string} />
      </div>
    {/if}

    {#if data.reasoning}
      <p class="text-text-secondary mt-1">{data.reasoning}</p>
    {/if}

    {#if data.techniques && Array.isArray(data.techniques)}
      <div class="mt-2">
        <span class="text-[10px] text-text-dim uppercase tracking-wider font-semibold">Techniques</span>
        <div class="flex flex-wrap gap-1 mt-1">
          {#each data.techniques as tech}
            <span class="px-1.5 py-0.5 rounded bg-neon-indigo/10 text-neon-indigo border border-neon-indigo/20 text-[10px]">
              {tech}
            </span>
          {/each}
        </div>
      </div>
    {/if}
  {:else}
    <p class="text-text-dim">Waiting for Analyze stage...</p>
  {/if}
</div>

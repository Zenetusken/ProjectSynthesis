<script lang="ts">
  import { forge } from '$lib/stores/forge.svelte';

  let result = $derived(forge.stageResults['explore']);
  let data = $derived((result?.data || {}) as Record<string, unknown>);
</script>

<div class="space-y-2 text-xs">
  {#if forge.stageStatuses['explore'] === 'running'}
    <div class="flex items-center gap-2 text-neon-cyan">
      <div class="w-3 h-3 border border-neon-cyan/30 border-t-neon-cyan rounded-full animate-spin"></div>
      <span>Exploring prompt context...</span>
    </div>
  {:else if result}
    <div class="space-y-1.5">
      {#if data.domain}
        <div class="flex justify-between">
          <span class="text-text-dim">Domain</span>
          <span class="text-text-secondary">{data.domain}</span>
        </div>
      {/if}
      {#if data.intent}
        <div class="flex justify-between">
          <span class="text-text-dim">Intent</span>
          <span class="text-text-secondary">{data.intent}</span>
        </div>
      {/if}
      {#if data.complexity}
        <div class="flex justify-between">
          <span class="text-text-dim">Complexity</span>
          <span class="text-text-secondary">{data.complexity}</span>
        </div>
      {/if}
      {#if data.summary}
        <p class="text-text-dim mt-1 italic">{data.summary}</p>
      {/if}
    </div>
  {:else}
    <p class="text-text-dim">Waiting to start...</p>
  {/if}
</div>

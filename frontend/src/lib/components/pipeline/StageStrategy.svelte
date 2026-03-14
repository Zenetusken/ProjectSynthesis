<script lang="ts">
  import { forge } from '$lib/stores/forge.svelte';
  import { getStrategyHex } from '$lib/utils/strategy';
  import StrategyBadge from '$lib/components/shared/StrategyBadge.svelte';

  let result = $derived(forge.stageResults['strategy']);
  let data = $derived((result?.data || {}) as Record<string, unknown>);

  let confidence = $derived(
    typeof data.confidence === 'number' ? data.confidence :
    typeof data.confidence_score === 'number' ? data.confidence_score : 0.85
  );
</script>

<div class="space-y-2 text-xs">
  {#if forge.stageStatuses['strategy'] === 'running'}
    <!-- Always show spinner during running state. Strategy streams raw JSON
         tokens which is meaningless to users. The complete structured result
         appears when the stage finishes (2-5s). -->
    <div class="flex items-center gap-2 text-neon-purple">
      <span class="w-3 h-3 rounded-full animate-spin" style="border: 1px solid transparent; border-top-color: #a855f7;"></span>
      <span>Selecting optimization strategy...</span>
    </div>
  {:else if result}
    {#if data.primary_framework}
      <div class="flex items-center gap-2">
        <StrategyBadge strategy={data.primary_framework as string} />
        <!-- Confidence bar (500ms ease fill per spec) -->
        <div class="flex-1 h-1.5 bg-bg-input overflow-hidden">
          <div
            class="h-full transition-all ease-out"
            style="width: {confidence * 100}%; background-color: {getStrategyHex(data.primary_framework as string)}; transition-duration: 500ms;"
          ></div>
        </div>
      </div>
    {/if}

    {#if data.rationale}
      <p class="text-xs text-text-secondary italic mt-1">{data.rationale}</p>
    {/if}

    {#if data.secondary_frameworks && Array.isArray(data.secondary_frameworks) && (data.secondary_frameworks as string[]).length > 0}
      <div class="mt-2">
        <span class="font-display text-[11px] font-bold uppercase text-text-dim">Techniques</span>
        <div class="flex flex-wrap gap-1 mt-1">
          {#each data.secondary_frameworks as tech}
            <span class="px-1.5 py-0.5 rounded-md bg-neon-indigo/10 text-neon-indigo border border-neon-indigo/20 text-[10px] font-mono">
              {tech}
            </span>
          {/each}
        </div>
      </div>
    {/if}

    {#if data.approach_notes}
      <p class="text-text-secondary mt-1 italic text-xs">{data.approach_notes}</p>
    {/if}
  {:else}
    <p class="text-text-secondary">Waiting for Analyze stage...</p>
  {/if}
</div>

<script lang="ts">
  import { forge } from '$lib/stores/forge.svelte';
  import CopyButton from '$lib/components/shared/CopyButton.svelte';
</script>

<div class="space-y-2 text-xs">
  {#if forge.stageStatuses['optimize'] === 'running'}
    <div class="space-y-2">
      <div class="flex items-center gap-2 text-neon-cyan">
        <div class="w-3 h-3 border border-neon-cyan/30 border-t-neon-cyan rounded-full animate-spin"></div>
        <span>Generating optimized prompt...</span>
      </div>

      {#if forge.streamingText}
        <div class="bg-bg-primary border border-border-accent rounded p-3 relative">
          <pre class="text-text-primary font-mono text-xs whitespace-pre-wrap leading-relaxed">{forge.streamingText}<span class="inline-block w-1.5 h-3.5 bg-neon-cyan animate-status-pulse ml-0.5"></span></pre>
        </div>
      {/if}
    </div>
  {:else if forge.stageStatuses['optimize'] === 'done'}
    <div class="bg-bg-primary border border-neon-green/20 rounded p-3 relative">
      <div class="flex items-center justify-between mb-2">
        <span class="text-[10px] text-neon-green uppercase tracking-wider font-semibold">Optimized Prompt</span>
        {#if forge.streamingText}
          <CopyButton text={forge.streamingText} />
        {/if}
      </div>
      <pre class="text-text-primary font-mono text-xs whitespace-pre-wrap leading-relaxed">{forge.streamingText || 'No output generated.'}</pre>
    </div>
  {:else}
    <p class="text-text-dim">Waiting for Strategy stage...</p>
  {/if}
</div>

<script lang="ts">
  import { forge } from '$lib/stores/forge.svelte';
  import CopyButton from '$lib/components/shared/CopyButton.svelte';
  import ScoreCircle from '$lib/components/shared/ScoreCircle.svelte';
</script>

<div class="p-4 space-y-4 animate-fade-in">
  <div class="flex items-center justify-between">
    <h2 class="text-sm font-semibold text-text-primary">Forge Artifact</h2>
    {#if forge.overallScore != null}
      <ScoreCircle score={forge.overallScore} size={32} />
    {/if}
  </div>

  {#if forge.streamingText}
    <div class="bg-bg-card border border-border-subtle rounded-lg p-4">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs text-text-secondary font-medium">Optimized Prompt</span>
        <CopyButton text={forge.streamingText} />
      </div>
      <pre class="text-sm text-text-primary font-mono whitespace-pre-wrap leading-relaxed">{forge.streamingText}</pre>
    </div>
  {:else}
    <div class="text-center py-12">
      <p class="text-sm text-text-dim">No artifact generated yet. Forge a prompt first.</p>
    </div>
  {/if}
</div>

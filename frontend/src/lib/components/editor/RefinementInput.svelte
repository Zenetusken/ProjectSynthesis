<script lang="ts">
  import { slide } from 'svelte/transition';
  import { refinement } from '$lib/stores/refinement.svelte';
  import ResizableTextarea from '$lib/components/shared/ResizableTextarea.svelte';

  const DIMENSIONS = [
    { key: 'clarity_score',     abbr: 'CLR' },
    { key: 'specificity_score', abbr: 'SPC' },
    { key: 'structure_score',   abbr: 'STR' },
    { key: 'faithfulness_score', abbr: 'FTH' },
    { key: 'conciseness_score', abbr: 'CNC' },
  ] as const;

  let { optimizationId }: { optimizationId: string } = $props();

  let message = $state('');

  function handleSend() {
    const trimmed = message.trim();
    if (!trimmed || refinement.refinementStreaming) return;
    refinement.startRefine(optimizationId, trimmed);
    message = '';
  }
</script>

{#if refinement.refinementOpen}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="border-t border-border-subtle bg-bg-secondary"
    class:refinement-streaming={refinement.refinementStreaming}
    transition:slide={{ duration: 200 }}
  >
    <!-- Header + dims + close — single compact row -->
    <div class="flex items-center gap-1.5 px-2 py-1.5">
      <span class="text-[9px] font-mono uppercase tracking-wider text-text-dim shrink-0">Refine</span>
      <div class="w-px h-3 bg-border-subtle shrink-0" aria-hidden="true"></div>
      {#each DIMENSIONS as dim}
        {@const isProtected = refinement.protectedDimensions.includes(dim.key)}
        <button
          class="px-1 py-px text-[9px] font-mono border transition-colors shrink-0"
          class:chip-protected={isProtected}
          class:chip-default={!isProtected}
          onclick={() => refinement.toggleProtectDimension(dim.key)}
          title="{isProtected ? 'Unprotect' : 'Protect'} {dim.key.replace(/_/g, ' ')}"
          aria-pressed={isProtected}
        >
          {dim.abbr}
        </button>
      {/each}
      <span class="text-[8px] font-mono text-text-dim/50 shrink-0">protect</span>
      <div class="flex-1"></div>
      <button
        class="w-4 h-4 flex items-center justify-center text-text-dim hover:text-text-secondary transition-colors shrink-0"
        onclick={() => refinement.closeRefinement()}
        aria-label="Close refinement panel"
        title="Close"
      >
        <svg width="8" height="8" viewBox="0 0 10 10" fill="none" aria-hidden="true">
          <line x1="1" y1="1" x2="9" y2="9" stroke="currentColor" stroke-width="1.5" stroke-linecap="square"/>
          <line x1="9" y1="1" x2="1" y2="9" stroke="currentColor" stroke-width="1.5" stroke-linecap="square"/>
        </svg>
      </button>
    </div>

    <!-- Input + send -->
    <div class="mx-2 mb-1.5 border" class:streaming-border={refinement.refinementStreaming} style="border-color: rgba(74, 74, 106, 0.2);">
      <ResizableTextarea
        bind:value={message}
        resize="drag"
        minHeight={40}
        maxHeight={300}
        placeholder="Describe how to improve..."
        disabled={refinement.refinementStreaming}
        onsubmit={handleSend}
        ariaLabel="Refinement message"
      />

      <!-- Send row -->
      <div class="flex items-center justify-between px-2 py-1 border-t border-border-subtle bg-bg-card">
        <span class="text-[8px] font-mono text-text-dim">
          {#if refinement.refinementStreaming}
            <span class="text-neon-cyan/60">streaming...</span>
          {:else}
            <kbd class="text-[8px]">&#8984; Enter</kbd>
          {/if}
        </span>
        <button
          class="h-5 px-2 text-[9px] font-mono border border-neon-cyan text-neon-cyan
                 hover:bg-neon-cyan/10 transition-colors
                 disabled:opacity-40 disabled:cursor-not-allowed"
          disabled={refinement.refinementStreaming || !message.trim()}
          onclick={handleSend}
          aria-label="Send refinement"
        >
          Send
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .chip-protected {
    background-color: rgba(0, 212, 170, 0.1);
    border-color: #00d4aa;
    color: #00d4aa;
  }

  .chip-default {
    background-color: transparent;
    border-color: rgba(74, 74, 106, 0.3);
    color: var(--color-text-dim);
  }

  .chip-default:hover {
    border-color: rgba(74, 74, 106, 0.6);
    color: var(--color-text-secondary);
  }

  @keyframes border-oscillate {
    0%, 100% { border-color: rgba(0, 229, 255, 0.3); }
    50% { border-color: rgba(0, 212, 170, 0.3); }
  }

  .streaming-border {
    animation: border-oscillate 1.4s ease-in-out infinite;
  }
</style>

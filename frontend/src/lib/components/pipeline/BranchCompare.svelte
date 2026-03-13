<script lang="ts">
  import { refinement } from '$lib/stores/refinement.svelte';
  import type { Branch } from '$lib/stores/refinement.svelte';
  import { compareBranches } from '$lib/api/client';
  import DiffView from '$lib/components/shared/DiffView.svelte';

  let {
    optimizationId,
    branchA,
    branchB,
    onclose,
  }: {
    optimizationId: string;
    branchA: Branch;
    branchB: Branch;
    onclose: () => void;
  } = $props();

  // All score dimension keys across both branches
  let allDimensions = $derived.by(() => {
    const keys = new Set<string>();
    if (branchA.scores) Object.keys(branchA.scores).forEach((k) => keys.add(k));
    if (branchB.scores) Object.keys(branchB.scores).forEach((k) => keys.add(k));
    return [...keys];
  });

  function scoreA(dim: string): number | null {
    return branchA.scores?.[dim] ?? null;
  }

  function scoreB(dim: string): number | null {
    return branchB.scores?.[dim] ?? null;
  }

  function delta(dim: string): number | null {
    const a = scoreA(dim);
    const b = scoreB(dim);
    if (a == null || b == null) return null;
    return b - a;
  }

  function deltaClass(d: number | null): string {
    if (d == null) return 'text-text-dim';
    if (d > 0) return 'text-neon-green';
    if (d < 0) return 'text-neon-red';
    return 'text-text-dim';
  }

  function deltaLabel(d: number | null): string {
    if (d == null) return '—';
    if (d > 0) return `+${d.toFixed(1)}`;
    return d.toFixed(1);
  }

  let selectingWinner = $state(false);

  async function handleSelect(branchId: string) {
    if (selectingWinner) return;
    selectingWinner = true;
    try {
      await refinement.selectWinner(optimizationId, branchId);
      onclose();
    } finally {
      selectingWinner = false;
    }
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) onclose();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') onclose();
  }
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<!-- Modal overlay — glass panel, no glow/shadow -->
<div
  class="fixed inset-0 z-50 flex items-center justify-center p-4"
  style="background: rgba(12, 12, 22, 0.7); backdrop-filter: blur(8px);"
  onclick={handleBackdropClick}
  onkeydown={handleKeydown}
  role="dialog"
  aria-modal="true"
  aria-label="Branch comparison"
  tabindex="-1"
>
  <!-- Panel -->
  <div
    class="relative w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col
           border border-neon-purple/20 bg-bg-card"
    style="animation: dialog-in 0.3s ease-out both;"
    onclick={(e) => e.stopPropagation()}
    role="presentation"
  >
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-2.5 border-b border-border-subtle shrink-0">
      <div class="flex items-center gap-3">
        <span class="font-display text-[11px] font-bold uppercase text-text-dim tracking-wider">
          Branch Compare
        </span>
        <span class="font-mono text-[10px] text-neon-purple/80 border border-neon-purple/20 px-1.5 py-0.5">
          {branchA.label}
        </span>
        <span class="text-text-dim/40 text-[10px]">vs</span>
        <span class="font-mono text-[10px] text-neon-blue/80 border border-neon-blue/20 px-1.5 py-0.5">
          {branchB.label}
        </span>
      </div>

      <!-- Close -->
      <button
        class="btn-icon w-6 h-6 flex items-center justify-center text-text-dim
               hover:text-text-primary transition-colors"
        onclick={onclose}
        aria-label="Close comparison"
        title="Close"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    </div>

    <!-- Scrollable content -->
    <div class="overflow-y-auto flex-1 min-h-0">

      <!-- Score table -->
      {#if allDimensions.length > 0}
        <div class="px-4 pt-3 pb-2">
          <div class="font-display text-[10px] font-bold uppercase text-text-dim tracking-wider mb-2">
            Score Comparison
          </div>
          <table class="w-full font-mono text-[10px] border-collapse" style="font-variant-numeric: tabular-nums;">
            <thead>
              <tr class="border-b border-border-subtle">
                <th class="text-left py-1.5 pr-3 text-text-dim font-medium uppercase tracking-wider text-[9px]">Dimension</th>
                <th class="text-right py-1.5 px-2 text-neon-purple/70 font-medium">{branchA.label}</th>
                <th class="text-right py-1.5 px-2 text-neon-blue/70 font-medium">{branchB.label}</th>
                <th class="text-right py-1.5 pl-2 text-text-dim font-medium">Delta</th>
              </tr>
            </thead>
            <tbody>
              {#each allDimensions as dim}
                {@const a = scoreA(dim)}
                {@const b = scoreB(dim)}
                {@const d = delta(dim)}
                <tr class="border-b border-border-subtle/50 hover:bg-bg-hover/30 transition-colors">
                  <td class="py-1.5 pr-3 text-text-secondary capitalize">
                    {dim.replace(/_/g, ' ')}
                  </td>
                  <td class="py-1.5 px-2 text-right text-text-secondary">
                    {a != null ? a.toFixed(1) : '—'}
                  </td>
                  <td class="py-1.5 px-2 text-right text-text-secondary">
                    {b != null ? b.toFixed(1) : '—'}
                  </td>
                  <td class="py-1.5 pl-2 text-right font-semibold {deltaClass(d)}">
                    {deltaLabel(d)}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}

      <!-- Prompt diff -->
      <div class="px-4 py-3 border-t border-border-subtle">
        <div class="font-display text-[10px] font-bold uppercase text-text-dim tracking-wider mb-2">
          Prompt Diff
        </div>
        <DiffView
          original={branchA.optimizedPrompt ?? ''}
          modified={branchB.optimizedPrompt ?? ''}
        />
      </div>

      <!-- Select buttons -->
      <div class="px-4 py-3 border-t border-border-subtle flex items-center justify-between gap-3 shrink-0">
        <div class="text-[10px] text-text-dim font-mono">
          Select winner to apply as the canonical optimized prompt
        </div>
        <div class="flex items-center gap-2">
          <button
            class="inline-flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-mono
                   border border-neon-purple/40 text-neon-purple bg-neon-purple/5
                   hover:bg-neon-purple/10 hover:border-neon-purple/60
                   transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            onclick={() => handleSelect(branchA.id)}
            disabled={selectingWinner}
            title="Select {branchA.label} as winner"
          >
            <span class="text-[9px]">◈</span>
            Select {branchA.label}
          </button>

          <button
            class="inline-flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-mono
                   border border-neon-cyan/40 text-neon-cyan bg-neon-cyan/5
                   hover:bg-neon-cyan/10 hover:border-neon-cyan/60
                   transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            onclick={() => handleSelect(branchB.id)}
            disabled={selectingWinner}
            title="Select {branchB.label} as winner"
          >
            <span class="text-[9px]">◈</span>
            Select {branchB.label}
          </button>
        </div>
      </div>

    </div>
  </div>
</div>

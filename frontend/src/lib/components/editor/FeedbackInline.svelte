<script lang="ts">
  import { feedback } from '$lib/stores/feedback.svelte';
  import { refinement } from '$lib/stores/refinement.svelte';
  import { forge } from '$lib/stores/forge.svelte';

  let { optimizationId }: { optimizationId: string } = $props();

  // Dimension definitions: abbreviation → score key
  const DIMENSIONS: { abbr: string; key: string; label: string }[] = [
    { abbr: 'CLR', key: 'clarity_score',      label: 'Clarity' },
    { abbr: 'SPC', key: 'specificity_score',  label: 'Specificity' },
    { abbr: 'STR', key: 'structure_score',    label: 'Structure' },
    { abbr: 'FTH', key: 'faithfulness_score', label: 'Faithfulness' },
    { abbr: 'CNC', key: 'conciseness_score',  label: 'Conciseness' },
  ];

  // Scores from the validate stage result
  let validateScores = $derived(
    (forge.stageResults['validate']?.data?.scores as Record<string, number> | undefined) ?? {}
  );

  // Current rating from the feedback store
  let currentRating = $derived(feedback.currentFeedback.rating);

  // Overridden dimensions
  let dimensionOverrides = $derived(feedback.currentFeedback.dimensionOverrides);

  function handleThumbUp() {
    const next: -1 | 0 | 1 = currentRating === 1 ? 0 : 1;
    feedback.setRating(next);
    if (next !== 0) {
      feedback.submit(optimizationId);
    }
  }

  function handleThumbDown() {
    const next: -1 | 0 | 1 = currentRating === -1 ? 0 : -1;
    feedback.setRating(next);
    if (next !== 0) {
      feedback.submit(optimizationId);
    }
  }

  function handleDimensionClick(key: string) {
    if (key in dimensionOverrides) {
      feedback.removeDimensionOverride(key);
    } else {
      // Default override score: bump by 1 if score available, else 5
      const currentScore = validateScores[key];
      const overrideScore = currentScore != null ? Math.min(10, Math.round(currentScore) + 1) : 5;
      feedback.setDimensionOverride(key, overrideScore);
    }
  }

  function handleRefine() {
    refinement.openRefinement();
  }
</script>

<!--
  FeedbackInline — 32px-height strip beneath the optimized prompt.
  Thumbs + dimension chips + Refine ghost button.
  Zero-effects: 1px solid borders only; no box-shadow, text-shadow, drop-shadow.
-->
<div
  class="flex items-center h-8 px-3 gap-2 border-t border-[rgba(74,74,106,0.15)] bg-[#11111e]"
  aria-label="Inline feedback controls"
>
  <!-- Thumbs Up -->
  <button
    class="inline-flex items-center justify-center w-6 h-6 transition-colors
           {currentRating === 1
             ? 'border border-[#22ff88] bg-[#22ff88]/8 text-[#22ff88]'
             : 'border border-[rgba(74,74,106,0.15)] text-[#7a7a9e] hover:border-[#22ff88]/40 hover:text-[#22ff88]'}"
    onclick={handleThumbUp}
    disabled={feedback.currentFeedback.submitting}
    aria-label="Thumbs up"
    aria-pressed={currentRating === 1}
    title="Positive feedback"
  >
    <svg width="12" height="12" viewBox="0 0 24 24" fill={currentRating === 1 ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round"
        d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z" />
      <path stroke-linecap="round" stroke-linejoin="round"
        d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
    </svg>
  </button>

  <!-- Thumbs Down -->
  <button
    class="inline-flex items-center justify-center w-6 h-6 transition-colors
           {currentRating === -1
             ? 'border border-[#ff3366] bg-[#ff3366]/8 text-[#ff3366]'
             : 'border border-[rgba(74,74,106,0.15)] text-[#7a7a9e] hover:border-[#ff3366]/40 hover:text-[#ff3366]'}"
    onclick={handleThumbDown}
    disabled={feedback.currentFeedback.submitting}
    aria-label="Thumbs down"
    aria-pressed={currentRating === -1}
    title="Negative feedback"
  >
    <svg width="12" height="12" viewBox="0 0 24 24" fill={currentRating === -1 ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round"
        d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z" />
      <path stroke-linecap="round" stroke-linejoin="round"
        d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
    </svg>
  </button>

  <!-- Divider -->
  <div class="w-px h-4 bg-[rgba(74,74,106,0.25)]" aria-hidden="true"></div>

  <!-- Dimension chips -->
  {#each DIMENSIONS as dim}
    {@const score = validateScores[dim.key]}
    {@const isOverridden = dim.key in dimensionOverrides}
    <button
      class="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-mono border transition-colors
             {isOverridden
               ? 'border-[#a855f7] bg-[#a855f7]/8 text-[#a855f7]'
               : score != null
                 ? 'border-[rgba(74,74,106,0.15)] text-[#8b8ba8] hover:border-[#00e5ff]/30 hover:text-[#00e5ff]'
                 : 'border-[rgba(74,74,106,0.10)] text-[#7a7a9e]/60 hover:border-[#00e5ff]/20 hover:text-[#8b8ba8]'}"
      onclick={() => handleDimensionClick(dim.key)}
      aria-label="{dim.label} dimension{isOverridden ? ' (overridden)' : ''}"
      aria-pressed={isOverridden}
      title="{dim.label}{score != null ? ': ' + score.toFixed(1) + '/10' : ''}{isOverridden ? ' (click to remove override)' : ' (click to override)'}"
    >
      <span>{dim.abbr}</span>
      {#if score != null}
        <span class="text-[9px] opacity-70">{Math.round(score)}</span>
      {/if}
    </button>
  {/each}

  <!-- Spacer -->
  <div class="flex-1" aria-hidden="true"></div>

  <!-- Refine ghost button -->
  <button
    class="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono border
           border-[rgba(74,74,106,0.15)] text-[#8b8ba8]
           hover:border-[#00e5ff]/30 hover:text-[#00e5ff]
           transition-colors"
    onclick={handleRefine}
    aria-label="Open refinement panel"
    title="Open refinement panel"
  >
    {#if refinement.branchCount > 0}
      <span class="text-[#a855f7]">◈</span>
      <span>{refinement.branchCount}</span>
    {:else}
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-5" />
        <path stroke-linecap="round" stroke-linejoin="round" d="M17.5 2.5a2.121 2.121 0 0 1 3 3L12 14l-4 1 1-4 7.5-7.5z" />
      </svg>
    {/if}
    Refine
  </button>
</div>

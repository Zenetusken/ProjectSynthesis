<script lang="ts">
  import { feedback } from '$lib/stores/feedback.svelte';
  import { forge } from '$lib/stores/forge.svelte';
  import { getScoreColor } from '$lib/utils/colors';
  import ResizableTextarea from '$lib/components/shared/ResizableTextarea.svelte';

  const DIMENSIONS: { key: string; abbr: string }[] = [
    { key: 'clarity_score', abbr: 'CLR' },
    { key: 'specificity_score', abbr: 'SPC' },
    { key: 'structure_score', abbr: 'STR' },
    { key: 'faithfulness_score', abbr: 'FTH' },
    { key: 'conciseness_score', abbr: 'CNC' },
  ];

  function clamp(val: number, min: number, max: number): number {
    return Math.max(min, Math.min(max, val));
  }

  function stepDimension(dim: string, delta: number) {
    const current = feedback.currentFeedback.dimensionOverrides[dim] ?? getBaseScore(dim);
    const next = clamp(current + delta, 0, 10);
    feedback.setDimensionOverride(dim, next);
  }

  function getBaseScore(dim: string): number {
    const scores = (forge.stageResults['validate']?.data as Record<string, unknown>)?.scores as Record<string, number> | undefined;
    if (!scores) return 5;
    return typeof scores[dim] === 'number' ? scores[dim] : 5;
  }

  function getDisplayScore(dim: string): number {
    return feedback.currentFeedback.dimensionOverrides[dim] ?? getBaseScore(dim);
  }

  function handleSave() {
    const optId = forge.optimizationId;
    if (optId) feedback.submit(optId);
  }
</script>

<div class="space-y-2">
  <h3 class="section-heading">Feedback</h3>

  <!-- Thumbs row — compact -->
  <div class="flex items-center gap-1.5">
    <button
      class="flex items-center justify-center w-7 h-7 border text-xs transition-colors {feedback.currentFeedback.rating === 1
        ? 'border-neon-green text-neon-green bg-neon-green/10'
        : 'border-border-subtle text-text-dim hover:border-neon-green/50 hover:text-neon-green'}"
      onclick={() => feedback.setRating(1)}
      aria-label="Thumbs up"
      aria-pressed={feedback.currentFeedback.rating === 1}
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
        <path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/>
      </svg>
    </button>
    <button
      class="flex items-center justify-center w-7 h-7 border text-xs transition-colors {feedback.currentFeedback.rating === 0
        ? 'border-text-secondary text-text-secondary bg-text-secondary/10'
        : 'border-border-subtle text-text-dim hover:border-text-secondary/50 hover:text-text-secondary'}"
      onclick={() => feedback.setRating(0)}
      aria-label="Neutral"
      aria-pressed={feedback.currentFeedback.rating === 0}
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm-3-9h6v2H9z"/>
      </svg>
    </button>
    <button
      class="flex items-center justify-center w-7 h-7 border text-xs transition-colors {feedback.currentFeedback.rating === -1
        ? 'border-neon-red text-neon-red bg-neon-red/10'
        : 'border-border-subtle text-text-dim hover:border-neon-red/50 hover:text-neon-red'}"
      onclick={() => feedback.setRating(-1)}
      aria-label="Thumbs down"
      aria-pressed={feedback.currentFeedback.rating === -1}
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
        <path d="M15 3H6c-.83 0-1.54.5-1.84 1.22l-3.02 7.05c-.09.23-.14.47-.14.73v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L9.83 23l6.59-6.59c.36-.36.58-.86.58-1.41V5c0-1.1-.9-2-2-2zm4 0v12h4V3h-4z"/>
      </svg>
    </button>
  </div>

  <!-- Dimension overrides — compact grid rows without score bars -->
  <div class="space-y-0.5">
    {#each DIMENSIONS as dim}
      {@const score = getDisplayScore(dim.key)}
      {@const isOverridden = dim.key in feedback.currentFeedback.dimensionOverrides}
      <div class="flex items-center gap-1 h-6">
        <span class="font-mono text-[9px] w-8 shrink-0 {isOverridden ? 'text-neon-cyan' : 'text-text-dim'}">{dim.abbr}</span>
        <!-- Score bar — thin inline indicator -->
        <div class="flex-1 h-1 bg-bg-primary overflow-hidden">
          <div class="h-full" style="width: {score * 10}%; background-color: {getScoreColor(score)};"></div>
        </div>
        <button
          class="w-5 h-5 flex items-center justify-center border border-border-subtle text-text-dim hover:border-neon-cyan/50 hover:text-neon-cyan text-[9px] leading-none transition-colors shrink-0"
          onclick={() => stepDimension(dim.key, -1)}
          aria-label="Decrease {dim.abbr}"
        >−</button>
        <span class="font-mono text-[9px] text-text-primary w-7 text-center shrink-0">{score}/10</span>
        <button
          class="w-5 h-5 flex items-center justify-center border border-border-subtle text-text-dim hover:border-neon-cyan/50 hover:text-neon-cyan text-[9px] leading-none transition-colors shrink-0"
          onclick={() => stepDimension(dim.key, 1)}
          aria-label="Increase {dim.abbr}"
        >+</button>
      </div>
    {/each}
  </div>

  <!-- Comment textarea — compact -->
  <ResizableTextarea
    bind:value={feedback.currentFeedback.comment}
    resize="drag"
    minHeight={32}
    maxHeight={160}
    mono
    placeholder="Optional comment..."
    class="p-1.5"
  />

  <!-- Save button -->
  <button
    class="w-full h-6 border border-neon-cyan text-neon-cyan text-[10px] font-display uppercase tracking-wider hover:bg-neon-cyan/10 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
    onclick={handleSave}
    disabled={feedback.currentFeedback.rating === null || feedback.currentFeedback.submitting}
  >
    {feedback.currentFeedback.submitting ? 'Saving...' : 'Save Feedback'}
  </button>
</div>

<script lang="ts">
  import { slide } from 'svelte/transition';
  import { feedback } from '$lib/stores/feedback.svelte';
  import { forge } from '$lib/stores/forge.svelte';

  // Color-coding per weight tier (mockup: cyan=top, yellow=high, purple=moderate, dim=low)
  function getBarColor(weight: number, maxWeight: number): { border: string; bg: string; text: string } {
    const ratio = weight / maxWeight;
    if (ratio >= 0.85) return { border: 'border-neon-cyan/40', bg: 'bg-neon-cyan/15', text: 'text-neon-cyan' };
    if (ratio >= 0.65) return { border: 'border-neon-yellow/30', bg: 'bg-neon-yellow/12', text: 'text-neon-yellow' };
    if (ratio >= 0.45) return { border: 'border-neon-purple/25', bg: 'bg-neon-purple/10', text: 'text-neon-purple' };
    return { border: 'border-text-dim/25', bg: 'bg-text-dim/15', text: 'text-text-dim' };
  }

  // Keys match backend adaptation_engine output
  const DEFAULT_WEIGHTS: Record<string, number> = {
    clarity_score: 0.20,
    specificity_score: 0.20,
    structure_score: 0.15,
    faithfulness_score: 0.25,
    conciseness_score: 0.20,
  };

  // 3-letter abbreviations matching FeedbackTier2 / RefinementInput
  const DIM_LABELS: Record<string, string> = {
    clarity_score: 'CLR',
    specificity_score: 'SPC',
    structure_score: 'STR',
    faithfulness_score: 'FTH',
    conciseness_score: 'CNC',
  };

  // Issue short labels
  const ISSUE_SHORT: Record<string, string> = {
    lost_key_terms: 'Term preservation',
    changed_meaning: 'Meaning fidelity',
    hallucinated_content: 'Addition prevention',
    lost_examples: 'Example preservation',
    too_verbose: 'Conciseness enforcement',
    too_vague: 'Specificity protection',
    wrong_tone: 'Tone matching',
    broken_structure: 'Structure preservation',
  };

  let showTechnicalDetails = $state(false);

  let adaptState = $derived(feedback.adaptationState);
  let summary = $derived(feedback.adaptationSummary);

  // Load adaptation data on mount
  $effect(() => {
    feedback.loadAdaptationSummary();
    feedback.loadAdaptationState();
  });

  // Priority bar max: use the highest weight to normalize bars
  let maxWeight = $derived.by(() => {
    if (!adaptState?.dimensionWeights) return 0.3;
    const weights = Object.values(adaptState.dimensionWeights) as number[];
    return Math.max(...weights, 0.3);
  });

  // Sorted dimension keys by weight for bar chart ordering (highest first in mockup)
  let sortedDims = $derived.by(() => {
    const dims = Object.keys(DEFAULT_WEIGHTS);
    if (!adaptState?.dimensionWeights) return dims;
    return [...dims].sort((a, b) =>
      (adaptState!.dimensionWeights![b] ?? 0) - (adaptState!.dimensionWeights![a] ?? 0)
    );
  });

  // Retry oracle data from the pipeline result
  let retryDiag = $derived(forge.retryDiagnostics as Record<string, unknown> | null);
</script>

<div class="space-y-2">
  <h3 class="section-heading">Adaptation</h3>

  {#if !adaptState && !summary}
    <p class="text-[10px] text-text-dim">No adaptation data.</p>
  {:else}
    <!-- ═══ YOUR PRIORITIES — color-coded bar chart ═══ -->
    <div class="space-y-1">
      <p class="text-[9px] text-text-dim uppercase font-mono tracking-widest">Your Priorities</p>
      <!-- Grid: fixed 5 columns. Bar area is 32px tall, labels below. -->
      <div class="grid grid-cols-5 gap-1">
        {#each sortedDims as dim}
          {@const liveW = adaptState?.dimensionWeights?.[dim] ?? DEFAULT_WEIGHTS[dim]}
          {@const pct = Math.round((liveW / maxWeight) * 100)}
          {@const colors = getBarColor(liveW, maxWeight)}
          {@const shift = summary?.priorities?.find((p) => p.dimension === dim)}
          <!-- Map pct to bar height within 32px max. Min 4px for visibility. -->
          {@const barH = Math.max(4, Math.round(pct * 0.32))}
          <div class="flex flex-col items-center">
            <!-- Bar area — fixed height, bar grows upward from bottom -->
            <div class="w-full relative" style="height: 32px;">
              <div
                class="absolute bottom-0 left-0 right-0 border transition-all duration-500 {colors.border} {colors.bg}"
                style="height: {barH}px;"
              ></div>
            </div>
            <!-- Label -->
            <span class="text-[8px] font-mono {colors.text} mt-0.5 leading-none">
              {DIM_LABELS[dim] ?? dim.replace('_score', '').slice(0, 3).toUpperCase()}
            </span>
            <!-- Shift (only show if rounds to ≥1%) -->
            {#if shift && Math.round(Math.abs(shift.shift) * 100) >= 1}
              <span class="text-[7px] font-mono leading-none {shift.direction === 'up' ? 'text-neon-green' : 'text-neon-red'}">
                {shift.direction === 'up' ? '+' : ''}{(shift.shift * 100).toFixed(0)}%
              </span>
            {/if}
          </div>
        {/each}
      </div>
    </div>

    <!-- ═══ 2-COLUMN GRID: Guardrails + Issue Resolution ═══ -->
    {#if summary && (summary.activeGuardrails.length > 0 || Object.keys(summary.issueResolution).length > 0)}
      <div class="grid grid-cols-2 gap-1.5">
        <!-- Active Guardrails -->
        <div class="border border-border-subtle p-1.5 space-y-1">
          <p class="text-[9px] font-mono text-text-dim uppercase tracking-widest">Active Guardrails</p>
          {#if summary.activeGuardrails.length > 0}
            {#each summary.activeGuardrails as guardrailId}
              {@const label = ISSUE_SHORT[guardrailId] ?? guardrailId}
              {@const count = summary.issueResolution[guardrailId] ?? 0}
              <div class="flex items-center gap-1 p-1 border border-neon-red/15 bg-neon-red/3">
                <span class="text-[9px] font-mono text-neon-red">&#9632;</span>
                <span class="text-[10px] text-text-primary flex-1 truncate">{label}</span>
                <span class="text-[8px] font-mono text-text-dim">{count}&times;</span>
              </div>
            {/each}
          {:else}
            <p class="text-[9px] font-mono text-text-dim">None active</p>
          {/if}
        </div>

        <!-- Issue Resolution -->
        <div class="border border-border-subtle p-1.5 space-y-1">
          <p class="text-[9px] font-mono text-text-dim uppercase tracking-widest">Issue Resolution</p>
          {#if Object.keys(summary.issueResolution).length > 0}
            {#each Object.entries(summary.issueResolution) as [issueId, count]}
              {@const label = ISSUE_SHORT[issueId] ?? issueId}
              {@const isActive = summary.activeGuardrails.includes(issueId)}
              <div class="flex items-center gap-1 p-1 border {isActive ? 'border-neon-yellow/15 bg-neon-yellow/3' : 'border-neon-green/15 bg-neon-green/3'}">
                <span class="text-[9px] font-mono {isActive ? 'text-neon-yellow' : 'text-neon-green'}">
                  {isActive ? '&#9679;' : '&#10003;'}
                </span>
                <span class="text-[10px] text-text-primary flex-1 truncate">{label}</span>
                <span class="text-[7px] font-mono {isActive ? 'text-neon-yellow' : 'text-neon-green'}">
                  {isActive ? `monitoring (${count}×)` : 'resolved'}
                </span>
              </div>
            {/each}
          {:else}
            <p class="text-[9px] font-mono text-text-dim">No issues reported</p>
          {/if}
        </div>
      </div>
    {/if}

    <!-- ═══ FRAMEWORK INTELLIGENCE — 4-col grid rows ═══ -->
    {#if summary && summary.topFrameworks.length > 0}
      <div class="space-y-1">
        <p class="text-[9px] font-mono text-text-dim uppercase tracking-widest">Framework Intelligence</p>
        <div class="space-y-0.5">
          {#each summary.topFrameworks as fw, i}
            {@const ratio = summary.frameworkPreferences[fw] ?? 0}
            {@const isPositive = ratio > 0}
            <div class="grid items-center gap-1.5 p-1 border border-border-subtle" style="grid-template-columns: 14px 1fr auto auto;">
              <span class="text-[9px] font-mono {isPositive ? 'text-neon-green' : 'text-neon-red'}">
                {isPositive ? '\u25B2' : '\u25BC'}
              </span>
              <span class="text-[10px] text-text-primary truncate">{fw}</span>
              <!-- Task type context from strategy affinities if available -->
              {#if adaptState?.strategyAffinities}
                {@const taskTypes = Object.entries(adaptState.strategyAffinities)
                  .filter(([_, aff]) => {
                    const a = aff as { preferred?: string[] } | null;
                    return a?.preferred?.includes(fw);
                  })
                  .map(([tt]) => tt)}
                {#if taskTypes.length > 0}
                  <span class="text-[9px] font-mono text-text-secondary">{taskTypes[0]}</span>
                {:else}
                  <span></span>
                {/if}
              {:else}
                <span></span>
              {/if}
              <span class="text-[9px] font-mono {isPositive ? 'text-neon-green' : 'text-neon-red'}">
                {ratio > 0 ? '+' : ''}{ratio.toFixed(0)}
              </span>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- ═══ QUALITY THRESHOLD — gradient fill + default label ═══ -->
    {@const thresholdVal = summary?.retryThreshold ?? adaptState?.retryThreshold ?? 5.0}
    {@const thresholdPct = Math.max(0, Math.min(100, ((thresholdVal - 3.0) / 5.0) * 100))}
    <div class="space-y-1">
      <p class="text-[9px] font-mono text-text-dim uppercase tracking-widest">Threshold</p>
      <div class="flex items-center gap-2">
        <div class="flex-1 relative h-[3px] bg-bg-primary overflow-hidden">
          <!-- Gradient fill from cyan to purple -->
          <div
            class="absolute top-0 left-0 h-full"
            style="width: {thresholdPct}%; background: linear-gradient(90deg, var(--color-neon-cyan), var(--color-neon-purple));"
          ></div>
          <!-- Threshold marker -->
          <div
            class="absolute h-[9px] w-px bg-neon-cyan"
            style="left: {thresholdPct}%; top: -3px;"
          ></div>
        </div>
        <span class="text-[10px] font-mono text-neon-cyan">{thresholdVal.toFixed(1)}</span>
        <span class="text-[9px] font-mono text-text-dim">def 5.0</span>
      </div>
    </div>

    <!-- ═══ STRATEGY AFFINITIES (detailed per-task breakdown) ═══ -->
    {#if adaptState?.strategyAffinities && Object.keys(adaptState.strategyAffinities).length > 0}
      <div class="space-y-1">
        <p class="text-[9px] font-mono text-text-dim uppercase tracking-widest">Strategy Affinities</p>
        {#each Object.entries(adaptState.strategyAffinities) as [taskType, affinity]}
          {@const aff = affinity as { preferred?: string[]; avoid?: string[] } | null}
          <div class="p-1.5 border border-border-subtle space-y-1">
            <span class="font-mono text-[10px] text-text-secondary capitalize">{taskType}</span>
            {#if aff?.preferred && aff.preferred.length > 0}
              <div class="flex flex-wrap gap-1">
                {#each aff.preferred as fw}
                  <span class="border border-neon-green/50 text-neon-green text-[9px] font-mono px-1 py-0">{fw}</span>
                {/each}
              </div>
            {/if}
            {#if aff?.avoid && aff.avoid.length > 0}
              <div class="flex flex-wrap gap-1">
                {#each aff.avoid as fw}
                  <span class="border border-neon-red/50 text-neon-red text-[9px] font-mono px-1 py-0 line-through">{fw}</span>
                {/each}
              </div>
            {/if}
          </div>
        {/each}
      </div>
    {/if}

    <!-- ═══ L3 TECHNICAL DETAILS (weights, elasticity, gate history) ═══ -->
    <button
      class="w-full flex items-center gap-1.5 text-[9px] font-mono text-text-dim hover:text-neon-cyan/70
             border border-border-subtle p-1.5 transition-colors duration-200 text-left"
      onclick={() => { showTechnicalDetails = !showTechnicalDetails; }}
      data-testid="adaptation-technical-toggle"
    >
      <span class="text-[9px] font-mono" class:rotate-90={showTechnicalDetails}>&#9656;</span>
      Technical Details (weights, elasticity, gate history)
    </button>
    {#if showTechnicalDetails && adaptState}
      <div class="p-1.5 bg-bg-primary border border-border-subtle text-[9px] font-mono text-text-dim space-y-2" transition:slide={{ duration: 200 }}>
        <!-- Dimension weights -->
        {#if adaptState.dimensionWeights}
          <div class="space-y-0.5">
            <div class="text-text-dim/70 uppercase tracking-wider">Dimension Weights</div>
            {#each Object.entries(adaptState.dimensionWeights) as [k, v]}
              {@const defaultW = DEFAULT_WEIGHTS[k] ?? 0.2}
              {@const delta = (v as number) - defaultW}
              <div class="flex justify-between pl-2">
                <span>{k.replace('_score', '')}</span>
                <span class="text-text-secondary">
                  {(v as number).toFixed(3)}
                  {#if Math.abs(delta) >= 0.005}
                    <span class="{delta > 0 ? 'text-neon-green' : 'text-neon-red'}">
                      ({delta > 0 ? '+' : ''}{delta.toFixed(3)})
                    </span>
                  {/if}
                </span>
              </div>
            {/each}
          </div>
        {/if}

        <!-- Retry oracle gate history -->
        {#if retryDiag}
          {@const gates = retryDiag.gate_sequence as string[] | undefined}
          {#if gates && gates.length > 0}
            <div class="space-y-0.5">
              <div class="text-text-dim/70 uppercase tracking-wider">Gate History</div>
              {#each gates as gate, i}
                <div class="flex justify-between pl-2">
                  <span>Gate {i + 1}</span>
                  <span class="text-text-secondary">{gate.replace(/_/g, ' ')}</span>
                </div>
              {/each}
            </div>
          {/if}
        {/if}

        <!-- Meta -->
        <div class="flex justify-between">
          <span>Retry threshold</span>
          <span class="text-text-secondary">{adaptState.retryThreshold.toFixed(2)}</span>
        </div>
        <div class="flex justify-between">
          <span>Feedback count</span>
          <span class="text-text-secondary">{adaptState.feedbackCount}</span>
        </div>
      </div>
    {/if}
  {/if}
</div>

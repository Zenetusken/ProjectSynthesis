<script lang="ts">
  import { slide } from 'svelte/transition';
  import { forge } from '$lib/stores/forge.svelte';
  import ScoreCircle from '$lib/components/shared/ScoreCircle.svelte';

  let { assessment }: {
    assessment: {
      verdict: string;
      confidence: string;
      headline: string;
      dimension_insights: Array<{
        dimension: string;
        score: number;
        weight: number;
        label: string;
        assessment: string;
        is_weak: boolean;
        is_strong: boolean;
        delta_from_previous: number | null;
        framework_avg: number | null;
        user_priority: string;
      }>;
      trade_offs: Array<{
        gained_dimension: string;
        lost_dimension: string;
        gained_delta: number;
        lost_delta: number;
        is_typical_for_framework: boolean;
        description: string;
      }>;
      retry_journey: {
        total_attempts: number;
        best_attempt: number;
        score_trajectory: number[];
        gate_sequence: string[];
        momentum_trend: string;
        summary: string;
      };
      framework_fit: {
        framework: string;
        task_type: string;
        fit_score: number;
        fit_label: string;
        user_rating_avg: number | null;
        sample_count: number;
        alternatives: string[];
        recommendation: string;
      } | null;
      improvement_signals: Array<{
        dimension: string;
        current_score: number;
        potential_gain: number;
        elasticity: number;
        effort_label: string;
        suggestion: string;
      }>;
      next_actions: Array<{
        action: string;
        rationale: string;
        priority: string;
        category: string;
      }>;
    };
  } = $props();

  // Expand/collapse states for progressive disclosure
  let expandedL1 = $state(false);
  let expandedDimension = $state<string | null>(null);

  // Verdict color maps
  const verdictClasses: Record<string, string> = {
    strong: 'text-neon-green',
    solid: 'text-neon-cyan',
    mixed: 'text-neon-yellow',
    weak: 'text-neon-red',
  };

  const verdictBorderColors: Record<string, string> = {
    strong: 'border-neon-green',
    solid: 'border-neon-cyan',
    mixed: 'border-neon-yellow',
    weak: 'border-neon-red',
  };

  const verdictBgColors: Record<string, string> = {
    strong: 'bg-neon-green/6',
    solid: 'bg-neon-cyan/6',
    mixed: 'bg-neon-yellow/6',
    weak: 'bg-neon-red/6',
  };

  // Full confidence labels per mockup
  const confidenceLabels: Record<string, string> = {
    high: 'HIGH CONFIDENCE',
    medium: 'MED CONFIDENCE',
    low: 'LOW CONFIDENCE',
  };

  // Priority tier badges — 4 visually distinct tiers per mockup
  const priorityBadges: Record<string, { label: string; colorClass: string }> = {
    high: { label: 'TOP PRIORITY', colorClass: 'text-neon-cyan border-neon-cyan/20 bg-neon-cyan/4' },
    high_score: { label: 'HIGH', colorClass: 'text-neon-yellow border-neon-yellow/20' },
    normal: { label: 'BALANCED', colorClass: 'text-text-secondary border-border-subtle' },
    low: { label: 'LOW', colorClass: 'text-text-dim/60 border-text-dim/15' },
  };

  // Resolve priority badge: strong-scoring non-top-priority dims get "HIGH" (yellow)
  function resolvePriorityBadge(insight: { user_priority: string; is_strong: boolean }): { label: string; colorClass: string } {
    if (insight.user_priority === 'high') return priorityBadges['high'];
    if (insight.is_strong && insight.user_priority === 'normal') return priorityBadges['high_score'];
    return priorityBadges[insight.user_priority] ?? priorityBadges['normal'];
  }

  // Elasticity label from value — thresholds tuned for the fallback range (0.15-0.7)
  function getElasticityLabel(e: number): string {
    if (e >= 0.6) return 'ELASTIC';
    if (e >= 0.4) return 'HIGH';
    if (e >= 0.25) return 'MODERATE';
    return 'LOW';
  }

  // Elasticity bar color class
  function getElasticityColor(e: number): string {
    if (e >= 0.4) return 'bg-neon-green';
    if (e >= 0.25) return 'bg-neon-yellow';
    return 'bg-neon-cyan/40';
  }

  // Score-based row border + background styling per mockup.
  // Strong dims get visible green border + tint, weak get red, balanced neutral.
  function getRowBorderClass(insight: { is_strong: boolean; is_weak: boolean }): string {
    if (insight.is_strong) return 'border-neon-green/25 bg-neon-green/[0.04]';
    if (insight.is_weak) return 'border-neon-red/25 bg-neon-red/[0.04]';
    return 'border-border-subtle';
  }

  // Score-to-color for dimension scores
  function getScoreClass(score: number): string {
    if (score >= 9) return 'text-neon-green';
    if (score >= 7) return 'text-neon-cyan';
    if (score >= 4) return 'text-neon-yellow';
    return 'text-neon-red';
  }

  // Framework fit label color
  function getFitLabelClass(label: string): string {
    const l = label?.toLowerCase() ?? '';
    if (l === 'excellent') return 'text-neon-green border-neon-green/20 bg-neon-green/6';
    if (l === 'good') return 'text-neon-cyan border-neon-cyan/20 bg-neon-cyan/6';
    if (l === 'fair') return 'text-neon-yellow border-neon-yellow/20 bg-neon-yellow/6';
    return 'text-neon-red border-neon-red/20 bg-neon-red/6';
  }

  let overallScore = $derived(forge.overallScore ?? 0);
  let verdictClass = $derived(verdictClasses[assessment.verdict] ?? 'text-neon-yellow');
  let verdictBorder = $derived(verdictBorderColors[assessment.verdict] ?? 'border-neon-yellow');
  let verdictBg = $derived(verdictBgColors[assessment.verdict] ?? 'bg-neon-yellow/6');

  // Retry sparkline: max score for normalizing bar heights
  let sparklineMax = $derived(
    Math.max(...(assessment.retry_journey.score_trajectory.length > 0
      ? assessment.retry_journey.score_trajectory
      : [10]))
  );

  // Sorted insights by user weight descending
  let sortedInsights = $derived(
    [...assessment.dimension_insights].sort((a, b) => b.weight - a.weight)
  );

  // Dimensions that lost in a trade-off
  let tradeOffLosers = $derived(
    new Set(assessment.trade_offs.map((t) => t.lost_dimension))
  );

  // Framework name from strategy stage
  let frameworkName = $derived(
    (forge.stageResults['strategy']?.data as Record<string, unknown>)?.primary_framework as string | undefined
  );

  // Last gate from retry journey
  let lastGate = $derived(
    assessment.retry_journey.gate_sequence.length > 0
      ? assessment.retry_journey.gate_sequence[assessment.retry_journey.gate_sequence.length - 1]
      : null
  );

  // Gate display name
  function formatGate(gate: string | null): string {
    if (!gate) return 'Single attempt';
    return gate.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }

  function toggleL1() {
    expandedL1 = !expandedL1;
    if (!expandedL1) expandedDimension = null;
  }

  function toggleDimension(dim: string) {
    expandedDimension = expandedDimension === dim ? null : dim;
  }
</script>

<!--
  ResultAssessment — progressive disclosure verdict engine.
  L0: Verdict bar (always visible)
  L1: Dimension map (click verdict to expand)
  L2: Journey + framework (click dimension row)
  Actions: Always visible below.
-->
<div class="border border-border-subtle bg-bg-card">
  <!-- ═══ L0 VERDICT BAR ═══ -->
  <button
    class="w-full flex items-center gap-2 px-2 py-1.5 transition-colors duration-200 hover:bg-bg-hover/50"
    onclick={toggleL1}
    aria-expanded={expandedL1}
    aria-label="Toggle result assessment details"
    data-testid="assessment-toggle"
  >
    <ScoreCircle score={overallScore} size={36} />

    <div class="flex-1 min-w-0 flex flex-col gap-px">
      <!-- Row 1: verdict + confidence + framework -->
      <div class="flex items-center gap-1.5 flex-wrap">
        <span class="text-[11px] font-mono font-bold tracking-wide {verdictClass}">
          {assessment.verdict.toUpperCase()}
        </span>
        <span class="text-[7px] font-mono text-text-dim">&#9679;</span>
        <span
          class="shrink-0 px-1 py-px text-[7px] font-mono font-bold uppercase border {verdictBorder} {verdictClass} {verdictBg}"
        >
          {confidenceLabels[assessment.confidence] ?? 'MED CONFIDENCE'}
        </span>
        {#if frameworkName}
          <span class="shrink-0 px-1 py-px text-[7px] font-mono text-text-secondary border border-border-subtle">
            {frameworkName}
          </span>
        {/if}
      </div>
      <!-- Row 2: headline -->
      <span class="text-[11px] text-text-primary truncate text-left">
        {assessment.headline}
      </span>
    </div>

    <!-- Retry sparkline + attempt count -->
    {#if assessment.retry_journey.score_trajectory.length > 1}
      <div class="shrink-0 flex items-end gap-px h-4" aria-label="Retry score sparkline">
        {#each assessment.retry_journey.score_trajectory as score, i}
          {@const barH = Math.max(2, (score / sparklineMax) * 16)}
          {@const isBest = i + 1 === assessment.retry_journey.best_attempt}
          <div
            class="w-1 {isBest ? 'bg-neon-green' : 'bg-text-dim/25'}"
            style="height: {barH}px;"
          ></div>
        {/each}
      </div>
      <span class="shrink-0 text-[8px] font-mono text-text-dim">
        {assessment.retry_journey.total_attempts} att.
      </span>
    {/if}

    <svg
      class="w-2.5 h-2.5 shrink-0 text-text-dim transition-transform duration-200"
      class:rotate-180={expandedL1}
      fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"
    >
      <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"></path>
    </svg>
  </button>

  <!-- ═══ L1 DIMENSION MAP ═══ -->
  {#if expandedL1}
    <div class="border-t border-border-subtle" transition:slide={{ duration: 200 }}>
      {#each sortedInsights as insight, i}
        {@const isTradeOff = tradeOffLosers.has(insight.dimension)}
        {@const isExpanded = expandedDimension === insight.dimension}
        {@const impSignal = assessment.improvement_signals.find(
          (s) => s.dimension === insight.dimension
        )}
        {@const elasticity = impSignal?.elasticity ?? 0}
        {@const rowBorder = getRowBorderClass(insight)}
        {@const priorityBadge = resolvePriorityBadge(insight)}

        <!-- Dimension row — color-coded per score tier -->
        <button
          class="w-full flex items-center gap-1.5 px-1.5 py-1 border transition-colors duration-200 text-left
                 hover:bg-bg-hover/50 {rowBorder}"
          onclick={() => toggleDimension(insight.dimension)}
          aria-expanded={isExpanded}
          data-testid="assessment-dimension-{insight.dimension}"
        >
          <!-- Score -->
          <span class="shrink-0 w-7 text-center text-[13px] font-mono font-bold {getScoreClass(insight.score)}">
            {insight.score.toFixed(0)}
          </span>
          <div class="w-px h-6 bg-border-subtle shrink-0" aria-hidden="true"></div>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1 flex-wrap">
              <span class="text-[11px] font-medium text-text-primary">{insight.label}</span>
              <span class="text-[7px] font-mono uppercase px-0.5 border {priorityBadge.colorClass}">
                {priorityBadge.label}
              </span>
              {#if insight.delta_from_previous != null && Math.abs(insight.delta_from_previous) >= 0.1}
                <span class="text-[8px] font-mono {insight.delta_from_previous > 0 ? 'text-neon-green' : 'text-neon-red'}">
                  {insight.delta_from_previous > 0 ? '+' : ''}{insight.delta_from_previous.toFixed(1)}
                </span>
              {/if}
              {#if isTradeOff}
                <span class="text-[7px] font-mono text-neon-yellow px-0.5 border border-neon-yellow/15 bg-neon-yellow/3">TRADE</span>
              {/if}
            </div>
            <p class="text-[9px] font-mono text-text-secondary leading-tight truncate">
              {insight.assessment}{#if insight.framework_avg != null} · Avg {insight.framework_avg.toFixed(1)}{/if}
            </p>
          </div>

          <!-- Elasticity — label + bar combined -->
          <div class="shrink-0 flex items-center gap-1">
            <span class="text-[7px] font-mono text-text-dim">{getElasticityLabel(elasticity)}</span>
            <div class="w-5 h-[2px] bg-bg-primary overflow-hidden" title="Elasticity: {elasticity.toFixed(2)}">
              <div class="h-full {getElasticityColor(elasticity)}" style="width: {Math.min(100, elasticity * 100)}%;"></div>
            </div>
          </div>
        </button>

        <!-- ═══ L2 JOURNEY + FRAMEWORK ═══ -->
        {#if isExpanded}
          <div class="px-1.5 py-1.5 bg-bg-primary/30 border-b border-border-subtle/50" transition:slide={{ duration: 150 }}>
            <div class="grid grid-cols-2 gap-1.5">
              <!-- Left: Retry Journey -->
              <div class="border border-border-subtle p-1.5 space-y-1">
                <p class="text-[8px] font-mono text-text-dim uppercase tracking-widest">Retry Journey</p>
                {#if assessment.retry_journey.score_trajectory.length > 1}
                  <div class="grid gap-0.5 items-end" style="grid-template-columns: repeat({assessment.retry_journey.score_trajectory.length}, 1fr); height: 32px;">
                    {#each assessment.retry_journey.score_trajectory as score, j}
                      {@const h = Math.max(4, (score / sparklineMax) * 28)}
                      {@const best = j + 1 === assessment.retry_journey.best_attempt}
                      <div class="flex flex-col items-center gap-0.5">
                        <div
                          class="w-full border {best ? 'bg-neon-green/12 border-neon-green/25' : j === 0 ? 'bg-text-dim/8 border-text-dim/15' : 'bg-neon-cyan/12 border-neon-cyan/20'}"
                          style="height: {h}px;"
                        ></div>
                        <span class="text-[8px] font-mono {best ? 'text-neon-green' : 'text-text-dim'}">
                          #{j + 1}{#if best} &#10003;{/if}
                        </span>
                      </div>
                    {/each}
                  </div>
                {/if}
                <!-- Journey text -->
                <div class="space-y-0.5">
                  <p class="text-[11px] text-text-primary">{assessment.retry_journey.summary}</p>
                  {#if lastGate}
                    <p class="text-[9px] font-mono text-text-secondary">
                      Accepted: {formatGate(lastGate)}
                    </p>
                  {/if}
                  {#if impSignal}
                    <p class="text-[9px] font-mono text-text-secondary">
                      Focus: {insight.label.toLowerCase()}{#if impSignal.potential_gain > 0}&nbsp;(could gain +{impSignal.potential_gain.toFixed(1)}){/if}
                    </p>
                  {:else if assessment.retry_journey.total_attempts === 1}
                    <p class="text-[9px] font-mono text-text-dim">
                      Retry to build improvement data
                    </p>
                  {/if}
                </div>
              </div>

              <!-- Right: Framework Fit -->
              <div class="border border-border-subtle p-1.5 space-y-1">
                <p class="text-[8px] font-mono text-text-dim uppercase tracking-widest">Framework Fit</p>
                {#if assessment.framework_fit}
                  <!-- Framework header with fit badge -->
                  <div class="flex items-center gap-1.5">
                    <span class="text-[11px] font-medium text-text-primary">
                      {assessment.framework_fit.framework}
                    </span>
                    <span class="text-[8px] font-mono font-bold uppercase px-1 border {getFitLabelClass(assessment.framework_fit.fit_label)}">
                      {assessment.framework_fit.fit_label.toUpperCase()}
                    </span>
                  </div>
                  <!-- Stats: user avg comparison + run count -->
                  <div class="space-y-0.5">
                    {#if assessment.framework_fit.user_rating_avg != null}
                      <p class="text-[10px] font-mono {assessment.framework_fit.user_rating_avg > 0 ? 'text-neon-green' : assessment.framework_fit.user_rating_avg < 0 ? 'text-neon-red' : 'text-text-secondary'}">
                        {assessment.framework_fit.user_rating_avg > 0 ? '+' : ''}{assessment.framework_fit.user_rating_avg.toFixed(1)} vs your average
                      </p>
                    {/if}
                    {#if assessment.framework_fit.sample_count > 0}
                      <p class="text-[9px] font-mono text-text-secondary">
                        {assessment.framework_fit.sample_count} prior runs{#if assessment.framework_fit.user_rating_avg != null} · {Math.round((1 + assessment.framework_fit.user_rating_avg) / 2 * assessment.framework_fit.sample_count)}/{assessment.framework_fit.sample_count} rated positive{/if}
                      </p>
                    {/if}
                  </div>
                  <!-- Recommendation -->
                  {#if assessment.framework_fit.recommendation}
                    <p class="text-[9px] font-mono text-text-dim">
                      {assessment.framework_fit.recommendation}
                    </p>
                  {/if}
                {:else}
                  <!-- Show framework name from strategy even without fit data -->
                  {#if frameworkName}
                    <div class="flex items-center gap-1.5">
                      <span class="text-[11px] font-medium text-text-primary">{frameworkName}</span>
                      <span class="text-[8px] font-mono text-text-dim border border-border-subtle px-1">FIRST RUN</span>
                    </div>
                    <p class="text-[9px] font-mono text-text-dim">Rate this result to build performance data</p>
                  {:else}
                    <p class="text-[9px] font-mono text-text-dim">No framework selected</p>
                  {/if}
                {/if}

                <!-- Trade-off section with gain/loss values -->
                {#each assessment.trade_offs.filter(
                  (t) => t.gained_dimension === insight.dimension || t.lost_dimension === insight.dimension
                ) as tradeOff}
                  <div class="border-t border-border-subtle pt-1.5 space-y-0.5">
                    <p class="text-[9px] font-mono text-text-dim uppercase tracking-widest">Trade-off</p>
                    <div class="flex items-center gap-1.5">
                      <span class="text-[10px] font-mono text-neon-green">{tradeOff.gained_dimension.replace('_score', '')} +{tradeOff.gained_delta.toFixed(1)}</span>
                      <span class="text-[10px] font-mono text-text-dim">&#8596;</span>
                      <span class="text-[10px] font-mono text-neon-red">{tradeOff.lost_dimension.replace('_score', '')} {tradeOff.lost_delta.toFixed(1)}</span>
                    </div>
                    <p class="text-[9px] font-mono text-text-secondary">
                      {tradeOff.is_typical_for_framework ? 'Typical pattern' : 'Atypical'} · {tradeOff.gained_delta + tradeOff.lost_delta > 0 ? 'Net positive' : 'Net negative'}
                    </p>
                  </div>
                {/each}
              </div>
            </div>
          </div>
        {/if}
      {/each}
    </div>
  {/if}

  <!-- ═══ ACTIONS BAR ═══ -->
  {#if assessment.next_actions.length > 0}
    <div class="grid grid-cols-2 border-t border-border-subtle">
      {#each assessment.next_actions.slice(0, 2) as action, i}
        <div
          class="px-2 py-1.5 {i === 0 ? 'border-r border-border-subtle bg-neon-green/[0.03]' : ''}"
        >
          <div class="flex items-center gap-1.5">
            <span class="text-[9px] font-mono px-1 leading-4 border {i === 0 ? 'text-neon-green border-neon-green/25' : 'text-text-dim border-border-subtle'}">
              {i + 1}
            </span>
            <span class="text-[11px] font-medium {i === 0 ? 'text-text-primary' : 'text-text-secondary'} truncate">
              {action.action}
            </span>
          </div>
          <p class="text-[9px] font-mono text-text-dim mt-0.5 line-clamp-2">
            {action.rationale}{#if i === 1}
              {@const sig = assessment.improvement_signals[0]}
              {#if sig && sig.potential_gain > 0} · could gain +{sig.potential_gain.toFixed(1)}{/if}
            {/if}
          </p>
        </div>
      {/each}
    </div>
  {/if}
</div>

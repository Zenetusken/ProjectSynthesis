<script lang="ts">
  import { forge } from '$lib/stores/forge.svelte';
  import StageCard from './StageCard.svelte';
  import StageExplore from './StageExplore.svelte';
  import StageAnalyze from './StageAnalyze.svelte';
  import StageStrategy from './StageStrategy.svelte';
  import StageOptimize from './StageOptimize.svelte';
  import StageValidate from './StageValidate.svelte';

  const stageLabels: Record<string, string> = {
    explore: 'Explore',
    analyze: 'Analyze',
    strategize: 'Strategize',
    optimize: 'Optimize',
    validate: 'Validate'
  };

  const stageIcons: Record<string, string> = {
    explore: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
    analyze: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
    strategize: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
    optimize: 'M13 10V3L4 14h7v7l9-11h-7z',
    validate: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
  };
</script>

<div class="space-y-3">
  {#each forge.stages as stage, i (stage)}
    {@const status = forge.stageStatuses[stage]}
    <StageCard
      name={stageLabels[stage]}
      icon={stageIcons[stage]}
      {status}
      index={i}
      isActive={forge.currentStage === stage}
    >
      {#if stage === 'explore'}
        <StageExplore />
      {:else if stage === 'analyze'}
        <StageAnalyze />
      {:else if stage === 'strategize'}
        <StageStrategy />
      {:else if stage === 'optimize'}
        <StageOptimize />
      {:else if stage === 'validate'}
        <StageValidate />
      {/if}
    </StageCard>
  {/each}
</div>

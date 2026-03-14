<script lang="ts">
  import { onMount } from 'svelte';
  import { editor } from '$lib/stores/editor.svelte';
  import { workbench } from '$lib/stores/workbench.svelte';
  import { patchAuthMe, fetchAuthMe, trackOnboardingEvent } from '$lib/api/client';
  import { user } from '$lib/stores/user.svelte';
  import { samplePrompts } from '$lib/utils/samplePrompts';
  import { pipelineStages } from '$lib/utils/strategyReference';

  interface Props {
    onComplete: () => void;
    githubConnected?: boolean;
    repoLinked?: boolean;
  }
  const { onComplete, githubConnected = false, repoLinked = false }: Props = $props();

  const STEP_KEY = 'pf_onboarding_step';

  // Restore step from localStorage on mount
  let step = $state((() => {
    if (typeof window === 'undefined') return 1;
    const stored = localStorage.getItem(STEP_KEY);
    if (stored) {
      const n = parseInt(stored, 10);
      if (n >= 1 && n <= 5) return n;
    }
    return 1;
  })());

  let stepEnteredAt = $state(Date.now());
  let displayName = $state('');
  let saving = $state(false);
  let error = $state('');

  // IDE tour hover state
  let hoveredZone = $state<string | null>(null);

  onMount(() => {
    trackOnboardingEvent('wizard_started', { restored_step: step > 1 });
    stepEnteredAt = Date.now();
  });

  const zones = [
    { id: 'activity', label: 'ACTIVITY BAR', desc: 'Switch panels: Files, History, Templates, GitHub, Settings', shortcut: 'Ctrl+Shift+*', col: '1', row: '1' },
    { id: 'navigator', label: 'NAVIGATOR', desc: 'Browse prompts, history, templates, and connected repos', shortcut: 'Ctrl+B', col: '2', row: '1' },
    { id: 'editor', label: 'EDITOR', desc: 'Write and edit prompts. Use @ for context injection', shortcut: 'Ctrl+N', col: '3', row: '1' },
    { id: 'inspector', label: 'INSPECTOR', desc: 'Scores, strategy details, and pipeline trace', shortcut: 'Ctrl+I', col: '4', row: '1' },
    { id: 'statusbar', label: 'STATUS BAR', desc: 'Provider, repo, strategy, and forge status at a glance', shortcut: '', col: '1 / -1', row: '2' },
  ];

  // Re-derive from shared constant with uppercase names for wizard display
  const stages = pipelineStages.map(s => ({ ...s, name: s.name.toUpperCase() }));

  function nextStep() {
    if (step < 5) {
      const durationMs = Date.now() - stepEnteredAt;
      trackOnboardingEvent(`wizard_step_${step}`, { duration_ms: durationMs });
      step++;
      stepEnteredAt = Date.now();
      if (typeof window !== 'undefined') localStorage.setItem(STEP_KEY, String(step));
      // Persist step to backend (best-effort)
      patchAuthMe({ onboarding_step: step }).catch(() => {});
      // Eagerly save display name when leaving step 1
      if (step === 2 && displayName.trim()) {
        patchAuthMe({ display_name: displayName.trim() }).catch(() => {});
      }
    }
  }

  function prevStep() {
    if (step > 1) {
      step--;
      stepEnteredAt = Date.now();
      if (typeof window !== 'undefined') localStorage.setItem(STEP_KEY, String(step));
    }
  }

  async function handleSkip() {
    const durationMs = Date.now() - stepEnteredAt;
    trackOnboardingEvent('wizard_skipped', { at_step: step, duration_ms: durationMs });
    patchAuthMe({ onboarding_completed: true, onboarding_step: null }).catch(() => {});
    user.onboardingCompleted = true;
    if (typeof window !== 'undefined') localStorage.removeItem(STEP_KEY);
    onComplete();
  }

  async function handleComplete(action: 'sample' | 'write' | 'github') {
    saving = true;
    error = '';
    try {
      if (displayName.trim()) {
        await patchAuthMe({
          display_name: displayName.trim(),
          onboarding_completed: true,
          onboarding_step: null,
        });
      } else {
        await patchAuthMe({ onboarding_completed: true, onboarding_step: null });
      }
      try { user.setProfile(await fetchAuthMe()); } catch { /* non-fatal */ }
    } catch (err) {
      // Non-fatal — mark completed locally so wizard doesn't re-show
      user.onboardingCompleted = true;
    }

    trackOnboardingEvent('wizard_completed', { action }).catch(() => {});

    if (action === 'sample' && samplePrompts.length > 0) {
      const sample = samplePrompts[0];
      editor.openTab({
        id: `sample-${sample.id}`,
        label: sample.title,
        type: 'prompt',
        promptText: sample.text,
        dirty: false,
      });
    } else if (action === 'write') {
      editor.openTab({
        id: `prompt-${Date.now()}`,
        label: 'New Prompt',
        type: 'prompt',
        promptText: '',
        dirty: false,
      });
    } else if (action === 'github') {
      workbench.setActivity('github');
    }

    saving = false;
    if (typeof window !== 'undefined') localStorage.removeItem(STEP_KEY);
    onComplete();
  }
</script>

<div class="w-full max-w-lg p-8 bg-bg-card border border-border-subtle animate-fade-in">
  {#if step === 1}
    <!-- Step 1: Welcome & Value Prop -->
    <div class="text-center mb-6">
      <h1 class="font-display text-lg tracking-[0.2em] uppercase text-transparent bg-clip-text bg-gradient-to-r from-neon-cyan to-neon-purple">
        PROJECT SYNTHESIS
      </h1>
      <p class="font-mono text-[9px] text-text-dim mt-1 tracking-[0.08em] uppercase">
        AI-Powered Prompt Engineering
      </p>
    </div>

    <div class="space-y-3 mb-6">
      <div class="step-box">
        <span class="font-display text-[11px] text-neon-cyan shrink-0 w-6">01</span>
        <div>
          <div class="font-display text-[10px] uppercase text-text-primary">5-Stage AI Pipeline</div>
          <div class="font-mono text-[9px] text-text-dim mt-0.5">Analyze, strategize, optimize, validate automatically</div>
        </div>
      </div>
      <div class="step-box">
        <span class="font-display text-[11px] text-neon-cyan shrink-0 w-6">02</span>
        <div>
          <div class="font-display text-[10px] uppercase text-text-primary">Codebase-Aware</div>
          <div class="font-mono text-[9px] text-text-dim mt-0.5">Connect GitHub for context-enriched optimization</div>
        </div>
      </div>
      <div class="step-box">
        <span class="font-display text-[11px] text-neon-cyan shrink-0 w-6">03</span>
        <div>
          <div class="font-display text-[10px] uppercase text-text-primary">Framework Library</div>
          <div class="font-mono text-[9px] text-text-dim mt-0.5">CO-STAR, RISEN, chain-of-thought and 7+ strategies</div>
        </div>
      </div>
    </div>

    <div class="mb-4">
      <label for="wizard-display-name" class="font-mono text-[8px] text-text-dim uppercase tracking-[0.08em] block mb-1">
        Display Name <span class="text-text-dim/50">(optional)</span>
      </label>
      <input
        id="wizard-display-name"
        type="text"
        maxlength="128"
        placeholder="Your name"
        bind:value={displayName}
        onkeydown={(e) => { if (e.key === 'Enter') nextStep(); }}
        class="w-full bg-bg-input border border-border-subtle px-2.5 py-1.5
               font-mono text-[11px] text-text-primary focus:outline-none
               focus:border-neon-cyan/30 placeholder:text-text-dim/40"
      />
    </div>

    <div class="flex items-center gap-2">
      <button
        onclick={nextStep}
        class="flex-1 btn-primary px-4 py-2.5 font-mono text-[11px] tracking-[0.07em] uppercase"
      >NEXT</button>
      <button
        onclick={handleSkip}
        class="btn-outline-subtle px-4 py-2.5 font-mono text-[10px] tracking-[0.05em] uppercase"
      >SKIP ALL</button>
    </div>

  {:else if step === 2}
    <!-- Step 2: IDE Tour -->
    <div class="mb-4">
      <h2 class="section-heading text-neon-cyan mb-1">Your Workspace</h2>
      <p class="font-mono text-[9px] text-text-dim">Hover each zone to learn what it does.</p>
    </div>

    <!-- Mini-map grid -->
    <div class="grid gap-1 mb-4" style="grid-template-columns: 36px 1fr 2fr 1fr; grid-template-rows: 100px 20px;">
      {#each zones as zone}
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div
          class="border border-border-subtle flex items-center justify-center cursor-pointer transition-colors duration-200
            {hoveredZone === zone.id ? 'border-neon-cyan/60 bg-neon-cyan/5' : 'hover:border-neon-cyan/30'}"
          style="grid-column: {zone.col}; grid-row: {zone.row};"
          onmouseenter={() => hoveredZone = zone.id}
          onmouseleave={() => hoveredZone = null}
        >
          <span class="font-mono text-[7px] text-text-dim/60 uppercase tracking-wider text-center px-0.5 leading-tight">
            {zone.id === 'activity' ? 'ACT' : zone.id === 'statusbar' ? 'STATUS' : zone.label.split(' ')[0]}
          </span>
        </div>
      {/each}
    </div>

    <!-- Hovered zone details -->
    <div class="min-h-[48px] mb-4 p-2 border border-border-subtle">
      {#if hoveredZone}
        {@const z = zones.find(z => z.id === hoveredZone)}
        {#if z}
          <div class="font-display text-[10px] uppercase text-text-primary">{z.label}</div>
          <div class="font-mono text-[9px] text-text-dim mt-0.5">{z.desc}</div>
          {#if z.shortcut}
            <kbd class="inline-block mt-1 px-1 bg-bg-input border border-border-subtle text-[8px] text-text-dim font-mono">{z.shortcut}</kbd>
          {/if}
        {/if}
      {:else}
        <div class="font-mono text-[9px] text-text-dim/40 italic">Hover a zone above to see details</div>
      {/if}
    </div>

    <div class="flex items-center gap-2">
      <button onclick={prevStep} class="btn-outline-subtle px-3 py-2 font-mono text-[10px] uppercase">BACK</button>
      <button onclick={nextStep} class="flex-1 btn-primary px-4 py-2 font-mono text-[11px] uppercase tracking-[0.07em]">NEXT</button>
    </div>

  {:else if step === 3}
    <!-- Step 3: Pipeline Explainer -->
    <div class="mb-4">
      <h2 class="section-heading text-neon-cyan mb-1">The Forge Pipeline</h2>
      <p class="font-mono text-[9px] text-text-dim">5 stages transform your prompt automatically.</p>
    </div>

    <div class="space-y-2 mb-4">
      {#each stages as stage, i}
        <div
          class="step-box animate-fade-in stagger-{i + 1}"
          style:border-left="1px solid {stage.color}"
        >
          <span class="font-display text-[10px] shrink-0 w-16 uppercase" style="color: {stage.color}">
            {stage.name}
          </span>
          <span class="font-mono text-[9px] text-text-dim leading-snug">{stage.desc}</span>
        </div>
      {/each}
    </div>

    <div class="flex items-center gap-2">
      <button onclick={prevStep} class="btn-outline-subtle px-3 py-2 font-mono text-[10px] uppercase">BACK</button>
      <button onclick={nextStep} class="flex-1 btn-primary px-4 py-2 font-mono text-[11px] uppercase tracking-[0.07em]">NEXT</button>
    </div>

  {:else if step === 4}
    <!-- Step 4: Train Your Pipeline -->
    <div class="mb-4">
      <h2 class="section-heading text-neon-cyan mb-1">Train Your Pipeline</h2>
      <p class="font-mono text-[9px] text-text-dim">Every rating teaches the system what quality means to you.</p>
    </div>

    <!-- The Loop: 3-node flow diagram -->
    <div class="flex items-center gap-1 mb-4">
      <div class="flex-1 border border-border-subtle p-1.5 text-center">
        <div class="text-[13px] mb-0.5">👍</div>
        <div class="font-display text-[9px] uppercase text-text-primary">Rate Result</div>
        <div class="font-mono text-[8px] text-text-dim mt-0.5">Thumbs up or down</div>
      </div>
      <span class="text-text-dim/30 text-xs shrink-0">→</span>
      <div class="flex-1 border border-neon-cyan/20 bg-neon-cyan/[0.03] p-1.5 text-center">
        <div class="text-[13px] mb-0.5">⚙</div>
        <div class="font-display text-[9px] uppercase text-neon-cyan">Pipeline Adapts</div>
        <div class="font-mono text-[8px] text-text-dim mt-0.5">Weights shift to your style</div>
      </div>
      <span class="text-text-dim/30 text-xs shrink-0">→</span>
      <div class="flex-1 border border-neon-green/20 bg-neon-green/[0.03] p-1.5 text-center">
        <div class="text-[13px] mb-0.5">✦</div>
        <div class="font-display text-[9px] uppercase text-neon-green">Better Output</div>
        <div class="font-mono text-[8px] text-text-dim mt-0.5">Next run matches you</div>
      </div>
    </div>

    <!-- Mini mock-up: feedback strip + priority bars -->
    <div class="border border-border-subtle p-1.5 mb-4 space-y-2">
      <div class="font-mono text-[8px] text-text-dim/60 uppercase tracking-widest">Live Preview</div>
      <!-- Mock feedback strip -->
      <div class="flex items-center gap-2 px-1 py-0.5 border-b border-border-subtle/50 pb-1.5">
        <div class="flex gap-1">
          <span class="w-5 h-5 border border-neon-green/40 bg-neon-green/8 flex items-center justify-center text-[10px]">+</span>
          <span class="w-5 h-5 border border-border-subtle flex items-center justify-center text-[10px] text-text-dim">−</span>
        </div>
        <span class="w-px h-3 bg-border-subtle"></span>
        <span class="w-[5px] h-[5px] rounded-full bg-neon-cyan"></span>
        <span class="font-mono text-[8px] text-text-dim">Adapted (3 feedbacks)</span>
      </div>
      <!-- Mock priority bars -->
      <div class="grid grid-cols-5 gap-1">
        <div class="flex flex-col items-center">
          <div class="w-full relative" style="height: 24px;">
            <div class="absolute bottom-0 left-0 right-0 border border-neon-cyan/40 bg-neon-cyan/15" style="height: 22px;"></div>
          </div>
          <span class="text-[7px] font-mono text-neon-cyan mt-0.5">CLR</span>
          <span class="text-[7px] font-mono text-neon-green">+8%</span>
        </div>
        <div class="flex flex-col items-center">
          <div class="w-full relative" style="height: 24px;">
            <div class="absolute bottom-0 left-0 right-0 border border-neon-yellow/30 bg-neon-yellow/12" style="height: 18px;"></div>
          </div>
          <span class="text-[7px] font-mono text-neon-yellow mt-0.5">FTH</span>
          <span class="text-[7px] font-mono text-neon-green">+5%</span>
        </div>
        <div class="flex flex-col items-center">
          <div class="w-full relative" style="height: 24px;">
            <div class="absolute bottom-0 left-0 right-0 border border-neon-purple/25 bg-neon-purple/10" style="height: 14px;"></div>
          </div>
          <span class="text-[7px] font-mono text-neon-purple mt-0.5">SPC</span>
        </div>
        <div class="flex flex-col items-center">
          <div class="w-full relative" style="height: 24px;">
            <div class="absolute bottom-0 left-0 right-0 border border-text-dim/25 bg-text-dim/15" style="height: 10px;"></div>
          </div>
          <span class="text-[7px] font-mono text-text-dim mt-0.5">STR</span>
        </div>
        <div class="flex flex-col items-center">
          <div class="w-full relative" style="height: 24px;">
            <div class="absolute bottom-0 left-0 right-0 border border-text-dim/25 bg-text-dim/15" style="height: 8px;"></div>
          </div>
          <span class="text-[7px] font-mono text-text-dim mt-0.5">CNC</span>
        </div>
      </div>
      <p class="font-mono text-[8px] text-text-dim/60 text-center">Your ratings shift dimension priorities — the pipeline focuses on what matters to you</p>
    </div>

    <!-- Pro tips -->
    <div class="space-y-1.5 mb-4">
      <div class="step-box">
        <span class="shrink-0 w-5 text-center text-[11px]">👍</span>
        <div>
          <div class="font-display text-[10px] uppercase text-text-primary">Thumbs Up Auto-Submits</div>
          <div class="font-mono text-[9px] text-text-dim mt-0.5">One click reinforces the optimization style — no form needed</div>
        </div>
      </div>
      <div class="step-box">
        <span class="shrink-0 w-5 text-center text-[11px]">👎</span>
        <div>
          <div class="font-display text-[10px] uppercase text-text-primary">Thumbs Down Opens Detail Mode</div>
          <div class="font-mono text-[9px] text-text-dim mt-0.5">Flag specific issues — lost terms, wrong tone, too verbose</div>
        </div>
      </div>
      <div class="step-box">
        <span class="shrink-0 w-5 text-center text-[11px]">📊</span>
        <div>
          <div class="font-display text-[10px] uppercase text-text-primary">Inspector → Adaptation</div>
          <div class="font-mono text-[9px] text-text-dim mt-0.5">See your priority bars, active guardrails, and framework preferences evolve</div>
        </div>
      </div>
    </div>

    <div class="flex items-center gap-2">
      <button onclick={prevStep} class="btn-outline-subtle px-3 py-2 font-mono text-[10px] uppercase">BACK</button>
      <button onclick={nextStep} class="flex-1 btn-primary px-4 py-2 font-mono text-[11px] uppercase tracking-[0.07em]">NEXT</button>
    </div>

  {:else if step === 5}
    <!-- Step 5: First Action -->
    <div class="mb-4">
      <h2 class="section-heading text-neon-cyan mb-1">Ready to Forge?</h2>
      <p class="font-mono text-[9px] text-text-dim">Choose how to get started.</p>
    </div>

    {#if error}
      <p class="font-mono text-[9px] text-neon-red mb-3">{error}</p>
    {/if}

    <div class="space-y-2 mb-4">
      <button
        onclick={() => handleComplete('sample')}
        disabled={saving}
        class="w-full flex items-start gap-3 p-3 text-left btn-outline-subtle"
      >
        <svg class="w-4 h-4 text-neon-cyan shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z"></path>
        </svg>
        <div>
          <div class="font-display text-[10px] uppercase text-text-primary">Start with a sample</div>
          <div class="font-mono text-[9px] text-text-dim mt-0.5">Load a pre-built prompt to see the pipeline in action</div>
        </div>
      </button>

      <button
        onclick={() => handleComplete('write')}
        disabled={saving}
        class="w-full flex items-start gap-3 p-3 text-left btn-outline-subtle"
      >
        <svg class="w-4 h-4 text-neon-green shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
        <div>
          <div class="font-display text-[10px] uppercase text-text-primary">Write your own</div>
          <div class="font-mono text-[9px] text-text-dim mt-0.5">Open a blank editor and start from scratch</div>
        </div>
      </button>

      <button
        onclick={() => handleComplete('github')}
        disabled={saving}
        class="w-full flex items-start gap-3 p-3 text-left btn-outline-subtle"
      >
        <svg class="w-4 h-4 text-neon-purple shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
        </svg>
        <div>
          <div class="font-display text-[10px] uppercase text-text-primary flex items-center gap-1.5">
            {#if repoLinked}
              Explore your codebase
              <span class="font-mono text-[8px] text-neon-cyan/60 normal-case tracking-normal">(recommended)</span>
            {:else if githubConnected}
              Link a repository
            {:else}
              Connect GitHub first
            {/if}
          </div>
          <div class="font-mono text-[9px] text-text-dim mt-0.5">
            {#if repoLinked}
              Your repo is linked — optimize with full codebase context
            {:else if githubConnected}
              GitHub connected — select a repo for codebase-aware optimization
            {:else}
              Link a repo for codebase-aware optimization
            {/if}
          </div>
        </div>
      </button>
    </div>

    <button onclick={prevStep} class="btn-outline-subtle px-3 py-2 font-mono text-[10px] uppercase">BACK</button>
  {/if}

  <!-- Step indicator -->
  <div class="flex items-center justify-center gap-1.5 mt-4">
    {#each [1, 2, 3, 4, 5] as s}
      <div class="w-1.5 h-1.5 {s === step ? 'bg-neon-cyan' : s < step ? 'bg-neon-cyan/30' : 'bg-border-subtle'} transition-colors"></div>
    {/each}
  </div>
</div>

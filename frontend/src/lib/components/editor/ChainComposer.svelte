<script lang="ts">
  let steps = $state<{ id: string; prompt: string }[]>([
    { id: 'step-1', prompt: '' }
  ]);

  function addStep() {
    steps = [...steps, { id: `step-${Date.now()}`, prompt: '' }];
  }

  function removeStep(id: string) {
    steps = steps.filter(s => s.id !== id);
  }
</script>

<div class="p-4 space-y-4 animate-fade-in">
  <div class="flex items-center justify-between">
    <h2 class="text-sm font-semibold text-text-primary">Chain Composer</h2>
    <button
      class="px-3 py-1 text-xs rounded bg-bg-card border border-border-subtle text-text-secondary hover:bg-bg-hover hover:text-text-primary transition-colors"
      onclick={addStep}
    >
      + Add Step
    </button>
  </div>

  <p class="text-xs text-text-dim">
    Build multi-step prompt chains. Each step's output feeds into the next.
  </p>

  <div class="space-y-3">
    {#each steps as step, i (step.id)}
      <div class="bg-bg-card border border-border-subtle rounded-lg p-3 animate-stagger-fade-in">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-medium text-text-secondary">Step {i + 1}</span>
          {#if steps.length > 1}
            <button
              class="text-[10px] text-neon-red/60 hover:text-neon-red transition-colors"
              onclick={() => removeStep(step.id)}
            >
              Remove
            </button>
          {/if}
        </div>
        <textarea
          class="w-full bg-bg-input border border-border-subtle rounded px-3 py-2 text-sm text-text-primary font-mono resize-none focus:outline-none focus:border-neon-cyan/30 h-20"
          placeholder="Enter prompt for step {i + 1}..."
          bind:value={step.prompt}
        ></textarea>
        {#if i < steps.length - 1}
          <div class="flex justify-center mt-2">
            <svg class="w-4 h-4 text-neon-cyan/40" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3"></path>
            </svg>
          </div>
        {/if}
      </div>
    {/each}
  </div>

  <button
    class="w-full py-2 rounded-lg text-xs font-semibold text-white transition-all hover:shadow-lg hover:shadow-neon-cyan/20 active:scale-[0.98]"
    style="background-image: var(--gradient-forge)"
  >
    Forge Chain
  </button>
</div>

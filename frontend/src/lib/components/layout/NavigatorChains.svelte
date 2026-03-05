<script lang="ts">
  import { editor } from '$lib/stores/editor.svelte';

  function newChain() {
    editor.openTab({
      id: `chain-${Date.now()}`,
      label: 'New Chain',
      type: 'chain',
      dirty: false
    });
  }
</script>

<div class="p-2 space-y-2">
  <div class="flex items-center justify-between px-1">
    <span class="text-[10px] uppercase tracking-wider text-text-dim font-semibold">Chains</span>
    <button
      class="w-5 h-5 flex items-center justify-center rounded text-text-dim hover:text-text-secondary hover:bg-bg-hover"
      aria-label="New chain"
      onclick={newChain}
    >
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"></path>
      </svg>
    </button>
  </div>

  <div class="text-xs text-text-secondary px-2 py-6 text-center">
    <p class="mb-2">Chain multiple prompts together for complex workflows.</p>
    <button
      class="text-neon-cyan hover:text-neon-cyan/80 transition-colors"
      onclick={newChain}
    >
      Create your first chain
    </button>
  </div>
</div>

<script lang="ts">
  import { editor, type EditorTab, type SubTab } from '$lib/stores/editor.svelte';
  import PromptEdit from './PromptEdit.svelte';
  import PromptPipeline from './PromptPipeline.svelte';
  import PromptHistory from './PromptHistory.svelte';

  let { tab }: { tab: EditorTab } = $props();

  const subTabs: { id: SubTab; label: string }[] = [
    { id: 'edit', label: 'Edit' },
    { id: 'pipeline', label: 'Pipeline' },
    { id: 'history', label: 'History' }
  ];
</script>

<div class="flex flex-col h-full">
  <!-- Sub-tab bar -->
  <div class="flex items-center h-8 border-b border-border-subtle bg-bg-secondary/50 px-2 gap-1 shrink-0">
    {#each subTabs as st}
      <button
        class="px-3 py-1 text-xs rounded-t transition-colors
          {editor.activeSubTab === st.id
            ? 'text-neon-cyan border-b border-neon-cyan bg-bg-primary'
            : 'text-text-dim hover:text-text-secondary'}"
        onclick={() => editor.setSubTab(st.id)}
      >
        {st.label}
      </button>
    {/each}
  </div>

  <!-- Sub-tab content -->
  <div class="flex-1 overflow-y-auto">
    {#if editor.activeSubTab === 'edit'}
      <PromptEdit {tab} />
    {:else if editor.activeSubTab === 'pipeline'}
      <PromptPipeline />
    {:else if editor.activeSubTab === 'history'}
      <PromptHistory />
    {/if}
  </div>
</div>

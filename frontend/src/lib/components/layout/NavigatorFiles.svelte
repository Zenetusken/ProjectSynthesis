<script lang="ts">
  import { editor } from '$lib/stores/editor.svelte';

  const sampleFiles = [
    { name: 'system-prompt.md', type: 'prompt' as const },
    { name: 'code-review.md', type: 'prompt' as const },
    { name: 'data-analysis.md', type: 'prompt' as const }
  ];

  function openFile(file: { name: string; type: 'prompt' }) {
    editor.openTab({
      id: `file-${file.name}`,
      label: file.name,
      type: file.type,
      promptText: '',
      dirty: false
    });
  }
</script>

<div class="p-2 space-y-0.5">
  <div class="flex items-center justify-between px-1 py-1">
    <span class="text-[10px] uppercase tracking-wider text-text-dim font-semibold">Workspace</span>
    <button
      class="w-5 h-5 flex items-center justify-center rounded text-text-dim hover:text-text-secondary hover:bg-bg-hover"
      aria-label="New file"
      onclick={() => editor.openTab({ id: `prompt-${Date.now()}`, label: 'New Prompt', type: 'prompt', promptText: '', dirty: false })}
    >
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"></path>
      </svg>
    </button>
  </div>

  {#each sampleFiles as file}
    <button
      class="w-full flex items-center gap-2 px-2 py-1 rounded text-xs text-text-secondary hover:bg-bg-hover hover:text-text-primary transition-colors"
      onclick={() => openFile(file)}
    >
      <svg class="w-3.5 h-3.5 text-neon-cyan/60 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
      </svg>
      <span class="truncate">{file.name}</span>
    </button>
  {/each}

  {#if sampleFiles.length === 0}
    <p class="text-xs text-text-dim px-2 py-4 text-center">No files in workspace</p>
  {/if}
</div>

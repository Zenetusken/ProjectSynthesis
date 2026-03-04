<script lang="ts">
  let { original = '', modified = '' }: { original?: string; modified?: string } = $props();

  // Simple line-by-line diff display
  let originalLines = $derived(original.split('\n'));
  let modifiedLines = $derived(modified.split('\n'));
</script>

<div class="font-mono text-xs space-y-0">
  <div class="grid grid-cols-2 gap-px bg-border-subtle rounded overflow-hidden">
    <!-- Original -->
    <div class="bg-bg-card p-2">
      <div class="text-[10px] text-neon-red/60 uppercase tracking-wider font-semibold mb-2">Original</div>
      {#each originalLines as line, i}
        <div class="py-0.5 px-1 text-text-secondary hover:bg-bg-hover/30 flex gap-2">
          <span class="text-text-dim/40 select-none w-4 text-right shrink-0">{i + 1}</span>
          <span class="whitespace-pre-wrap break-all">{line}</span>
        </div>
      {/each}
    </div>

    <!-- Modified -->
    <div class="bg-bg-card p-2">
      <div class="text-[10px] text-neon-green/60 uppercase tracking-wider font-semibold mb-2">Modified</div>
      {#each modifiedLines as line, i}
        <div class="py-0.5 px-1 text-text-secondary hover:bg-bg-hover/30 flex gap-2">
          <span class="text-text-dim/40 select-none w-4 text-right shrink-0">{i + 1}</span>
          <span class="whitespace-pre-wrap break-all">{line}</span>
        </div>
      {/each}
    </div>
  </div>
</div>

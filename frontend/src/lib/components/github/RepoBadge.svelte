<script lang="ts">
  let { name, isPrivate = false }: { name: string; isPrivate?: boolean } = $props();
</script>

<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-bg-card border border-border-subtle text-text-secondary">
  {#if isPrivate}
    <svg class="w-2.5 h-2.5 text-neon-yellow" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 1C8.676 1 6 3.676 6 7v2H4v14h16V9h-2V7c0-3.324-2.676-6-6-6zm0 2c2.276 0 4 1.724 4 4v2H8V7c0-2.276 1.724-4 4-4z"></path>
    </svg>
  {:else}
    <svg class="w-2.5 h-2.5 text-text-dim" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
    </svg>
  {/if}
  <span class="truncate max-w-[120px]">{name}</span>
</span>

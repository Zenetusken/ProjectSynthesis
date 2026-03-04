<script lang="ts">
  import { github } from '$lib/stores/github.svelte';
</script>

<div class="flex items-center gap-2 px-1">
  <span class="w-2 h-2 rounded-full shrink-0 {github.isConnected ? 'bg-neon-green' : 'bg-text-dim/30'}"></span>
  <div class="flex-1 min-w-0">
    {#if github.isConnected}
      <span class="text-xs text-text-primary">{github.username}</span>
      <span class="text-[10px] text-text-dim ml-1">Connected</span>
    {:else}
      <span class="text-xs text-text-dim">Not connected</span>
    {/if}
  </div>
</div>

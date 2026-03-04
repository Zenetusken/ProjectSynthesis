<script lang="ts">
  import { workbench } from '$lib/stores/workbench.svelte';
  import { editor } from '$lib/stores/editor.svelte';
  import { forge } from '$lib/stores/forge.svelte';
  import ProviderBadge from '$lib/components/shared/ProviderBadge.svelte';
</script>

<footer
  class="h-[24px] flex items-center justify-between px-2 bg-bg-secondary border-t border-border-subtle text-[10px] select-none shrink-0"
  aria-label="Status Bar"
>
  <div class="flex items-center gap-3">
    <!-- Connection status -->
    <div class="flex items-center gap-1">
      <span class="w-1.5 h-1.5 rounded-full {workbench.isConnected ? 'bg-neon-green' : 'bg-neon-red'}"></span>
      <span class="text-text-dim">{workbench.isConnected ? 'Connected' : 'Disconnected'}</span>
    </div>

    <!-- Provider info -->
    {#if workbench.provider !== 'unknown'}
      <ProviderBadge provider={workbench.provider} />
    {/if}

    <!-- Forge status -->
    {#if forge.isForging}
      <div class="flex items-center gap-1 text-neon-cyan">
        <span class="animate-status-pulse">Forging</span>
        <span class="capitalize">{forge.currentStage || '...'}</span>
      </div>
    {/if}
  </div>

  <div class="flex items-center gap-3">
    <!-- Active tab info -->
    {#if editor.activeTab}
      <span class="text-text-dim">{editor.activeTab.label}</span>
    {/if}

    <!-- Tab count -->
    <span class="text-text-dim">{editor.openTabs.length} tab{editor.openTabs.length !== 1 ? 's' : ''}</span>

    <!-- Model -->
    {#if workbench.providerModel}
      <span class="text-text-dim font-mono">{workbench.providerModel}</span>
    {/if}
  </div>
</footer>

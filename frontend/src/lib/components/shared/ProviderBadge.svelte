<script lang="ts">
  let { provider }: { provider: string } = $props();

  let label = $derived(
    provider === 'anthropic' ? 'CLI' :
    provider === 'openai' ? 'API' :
    'Unknown'
  );

  let color = $derived(
    provider === 'anthropic' ? 'bg-neon-orange/10 text-neon-orange border-neon-orange/20' :
    provider === 'openai' ? 'bg-neon-green/10 text-neon-green border-neon-green/20' :
    'bg-bg-card text-text-dim border-border-subtle'
  );
</script>

<span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border {color}">
  {label}
</span>

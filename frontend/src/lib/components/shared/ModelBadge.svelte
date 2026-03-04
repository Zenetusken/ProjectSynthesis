<script lang="ts">
  let { model }: { model: string } = $props();

  let color = $derived(
    model.includes('claude') ? 'bg-neon-orange/10 text-neon-orange border-neon-orange/20' :
    model.includes('gpt') ? 'bg-neon-green/10 text-neon-green border-neon-green/20' :
    'bg-bg-card text-text-secondary border-border-subtle'
  );
</script>

<span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-medium border {color}">
  {model}
</span>

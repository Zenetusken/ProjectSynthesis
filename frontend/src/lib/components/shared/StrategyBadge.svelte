<script lang="ts">
  let { strategy }: { strategy: string } = $props();

  const colorMap: Record<string, string> = {
    auto: 'bg-neon-cyan/10 text-neon-cyan border-neon-cyan/20',
    enhance: 'bg-neon-green/10 text-neon-green border-neon-green/20',
    'chain-of-thought': 'bg-neon-purple/10 text-neon-purple border-neon-purple/20',
    'few-shot': 'bg-neon-orange/10 text-neon-orange border-neon-orange/20',
    structured: 'bg-neon-blue/10 text-neon-blue border-neon-blue/20',
    'role-based': 'bg-neon-pink/10 text-neon-pink border-neon-pink/20'
  };

  let classes = $derived(colorMap[strategy] || 'bg-bg-card text-text-secondary border-border-subtle');
</script>

<span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border {classes}">
  {strategy}
</span>

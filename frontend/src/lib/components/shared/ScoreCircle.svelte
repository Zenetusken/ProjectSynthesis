<script lang="ts">
  let { score, size = 20 }: { score: number; size?: number } = $props();

  let color = $derived(
    score >= 8 ? 'text-neon-green' :
    score >= 6 ? 'text-neon-cyan' :
    score >= 4 ? 'text-neon-yellow' :
    'text-neon-red'
  );

  let bgColor = $derived(
    score >= 8 ? 'bg-neon-green/10 border-neon-green/30' :
    score >= 6 ? 'bg-neon-cyan/10 border-neon-cyan/30' :
    score >= 4 ? 'bg-neon-yellow/10 border-neon-yellow/30' :
    'bg-neon-red/10 border-neon-red/30'
  );

  let fontSize = $derived(size <= 24 ? 'text-[9px]' : size <= 36 ? 'text-xs' : 'text-sm');
</script>

<div
  class="inline-flex items-center justify-center rounded-full border font-semibold shrink-0 {color} {bgColor} {fontSize}"
  style="width: {size}px; height: {size}px;"
  title="Score: {score}/10"
>
  {score.toFixed(score % 1 === 0 ? 0 : 1)}
</div>

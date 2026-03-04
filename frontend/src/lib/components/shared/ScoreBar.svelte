<script lang="ts">
  let { score, max = 10 }: { score: number; max?: number } = $props();

  let pct = $derived(Math.min(100, Math.max(0, (score / max) * 100)));

  let barColor = $derived(
    score / max >= 0.8 ? 'bg-neon-green' :
    score / max >= 0.6 ? 'bg-neon-cyan' :
    score / max >= 0.4 ? 'bg-neon-yellow' :
    'bg-neon-red'
  );
</script>

<div class="w-full h-1.5 bg-bg-primary rounded-full overflow-hidden">
  <div
    class="h-full rounded-full transition-all duration-500 {barColor}"
    style="width: {pct}%"
  ></div>
</div>

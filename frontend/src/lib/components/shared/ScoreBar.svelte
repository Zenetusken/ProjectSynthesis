<script lang="ts">
  import { getScoreColor } from '$lib/utils/colors';

  let { score, max = 10 }: { score: number; max?: number } = $props();

  let pct = $derived(Math.min(100, Math.max(0, (score / max) * 100)));
  let barColor = $derived(getScoreColor(score));
</script>

<div class="w-full h-1.5 bg-bg-primary overflow-hidden" data-testid="score-bar">
  <div
    class="h-full origin-left"
    style="width: {pct}%; background-color: {barColor}; animation: progress-fill 0.5s cubic-bezier(0.16, 1, 0.3, 1) both; transition: width 500ms ease;"
  ></div>
</div>

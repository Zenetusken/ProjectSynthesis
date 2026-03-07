<script lang="ts">
  import { getScoreColor } from '$lib/utils/colors';

  let { score, size = 20 }: { score: number; size?: number } = $props();

  let scoreColor = $derived(getScoreColor(score));
  let fontSize = $derived(size <= 24 ? 10 : size <= 36 ? 12 : 14);
</script>

<div
  class="score-circle inline-flex items-center justify-center rounded-full font-mono font-bold shrink-0"
  style="width: {size}px; height: {size}px; color: {scoreColor}; font-size: {fontSize}px; box-shadow: inset 0 0 0 1px {scoreColor}; background: color-mix(in srgb, {scoreColor} 8%, transparent);"
  title="Score: {score}/10"
  aria-label="Score: {score} out of 10"
  role="img"
  data-testid="score-circle"
>
  {score.toFixed(score % 1 === 0 ? 0 : 1)}
</div>

export function getScoreColor(score: number): string {
  if (score >= 9) return '#22ff88';
  if (score >= 7) return '#00e5ff';
  if (score >= 4) return '#fbbf24';
  return '#ff3366';
}

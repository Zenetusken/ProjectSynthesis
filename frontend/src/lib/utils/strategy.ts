/**
 * Canonical strategy → chromatic color mapping.
 * Single source of truth used by StageTrack, StageStrategy,
 * Inspector, StatusBar, and NavigatorHistory.
 */
export const STRATEGY_HEX: Record<string, string> = {
  'auto':                 '#00e5ff',
  'chain-of-thought':     '#00e5ff',
  'co-star':              '#a855f7',
  'CO-STAR':              '#a855f7',
  'risen':                '#22ff88',
  'RISEN':                '#22ff88',
  'role-task-format':     '#ff3366',
  'few-shot-scaffolding': '#fbbf24',
  'step-by-step':         '#ff8c00',
  'structured-output':    '#4d8eff',
  'constraint-injection': '#ff6eb4',
  'context-enrichment':   '#00d4aa',
  'persona-assignment':   '#7b61ff',
};

/** Returns the chromatic hex for a strategy, falling back to neon-cyan. */
export function getStrategyHex(fw: string | null | undefined): string {
  if (!fw) return '#00e5ff';
  return STRATEGY_HEX[fw] ?? STRATEGY_HEX[fw.toLowerCase()] ?? '#00e5ff';
}

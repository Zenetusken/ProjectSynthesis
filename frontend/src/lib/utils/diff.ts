export interface DiffLine {
  type: 'add' | 'remove' | 'equal';
  value: string;
  lineNumber?: number;
}

/**
 * Compute a simple line-level diff between two strings.
 * For a more robust implementation, use the 'diff' npm package.
 */
export function computeLineDiff(original: string, modified: string): DiffLine[] {
  const origLines = original.split('\n');
  const modLines = modified.split('\n');
  const result: DiffLine[] = [];
  const maxLen = Math.max(origLines.length, modLines.length);

  for (let i = 0; i < maxLen; i++) {
    const orig = origLines[i];
    const mod = modLines[i];

    if (orig === undefined && mod !== undefined) {
      result.push({ type: 'add', value: mod, lineNumber: i + 1 });
    } else if (orig !== undefined && mod === undefined) {
      result.push({ type: 'remove', value: orig, lineNumber: i + 1 });
    } else if (orig !== mod) {
      result.push({ type: 'remove', value: orig, lineNumber: i + 1 });
      result.push({ type: 'add', value: mod!, lineNumber: i + 1 });
    } else {
      result.push({ type: 'equal', value: orig, lineNumber: i + 1 });
    }
  }

  return result;
}

/**
 * Calculate similarity percentage between two strings.
 */
export function similarityScore(a: string, b: string): number {
  if (a === b) return 100;
  if (!a || !b) return 0;

  const longer = a.length > b.length ? a : b;
  const shorter = a.length > b.length ? b : a;

  if (longer.length === 0) return 100;

  let matches = 0;
  for (let i = 0; i < shorter.length; i++) {
    if (shorter[i] === longer[i]) matches++;
  }

  return Math.round((matches / longer.length) * 100);
}

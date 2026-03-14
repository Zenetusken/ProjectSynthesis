export interface ContextChip {
  id: string;
  label: string;
  type: string;
  size?: number;    // optional byte size (M7)
  content?: string; // N24: actual content for file/instruction/url chips
  source?: string;  // optional origin tag (e.g. 'github' for repo file chips)
  filePath?: string; // original file path (used to deselect github file chips)
}

class ContextStore {
  chips = $state<ContextChip[]>([]);

  addChip(type: string, label?: string, size?: number, content?: string, source?: string, filePath?: string) {
    const chipLabel = label || `@${type}`;
    this.chips = [
      ...this.chips,
      {
        id: `ctx-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        label: chipLabel,
        type,
        size,
        content,
        source,
        filePath,
      },
    ];
  }

  removeChip(id: string) {
    this.chips = this.chips.filter(c => c.id !== id);
  }

  clear() {
    this.chips = [];
  }
}

export const context = new ContextStore();

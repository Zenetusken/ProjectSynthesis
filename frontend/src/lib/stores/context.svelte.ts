export interface ContextChip {
  id: string;
  label: string;
  type: string;
  size?: number; // M7: optional byte size
}

class ContextStore {
  chips = $state<ContextChip[]>([]);

  addChip(type: string, label?: string, size?: number) {
    const chipLabel = label || `@${type}`;
    this.chips = [
      ...this.chips,
      {
        id: `ctx-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        label: chipLabel,
        type,
        size,
      },
    ];
  }

  removeChip(id: string) {
    this.chips = this.chips.filter(c => c.id !== id);
  }

  getChips(): ContextChip[] {
    return this.chips;
  }

  clear() {
    this.chips = [];
  }
}

export const context = new ContextStore();

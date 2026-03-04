export interface PaletteCommand {
  id: string;
  label: string;
  shortcut?: string;
  category: string;
  action: () => void;
}

class CommandPaletteStore {
  isOpen = $state(false);
  query = $state('');
  commands = $state<PaletteCommand[]>([]);
  selectedIndex = $state(0);

  get filteredCommands(): PaletteCommand[] {
    if (!this.query) return this.commands;
    const q = this.query.toLowerCase();
    return this.commands.filter(
      c => c.label.toLowerCase().includes(q) || c.category.toLowerCase().includes(q)
    );
  }

  open() {
    this.isOpen = true;
    this.query = '';
    this.selectedIndex = 0;
  }

  close() {
    this.isOpen = false;
    this.query = '';
    this.selectedIndex = 0;
  }

  toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  setQuery(q: string) {
    this.query = q;
    this.selectedIndex = 0;
  }

  moveUp() {
    if (this.selectedIndex > 0) {
      this.selectedIndex--;
    }
  }

  moveDown() {
    const max = this.filteredCommands.length - 1;
    if (this.selectedIndex < max) {
      this.selectedIndex++;
    }
  }

  executeSelected() {
    const cmds = this.filteredCommands;
    if (cmds.length > 0 && this.selectedIndex < cmds.length) {
      cmds[this.selectedIndex].action();
      this.close();
    }
  }

  registerCommands(cmds: PaletteCommand[]) {
    this.commands = cmds;
  }
}

export const commandPalette = new CommandPaletteStore();

export type ToastType = 'info' | 'success' | 'error' | 'warning';

export interface ToastItem {
  id: number;
  message: string;
  type: ToastType;
  dismissing: boolean;
}

const MAX_VISIBLE = 3;
let nextId = 0;

class ToastStore {
  toasts = $state<ToastItem[]>([]);

  show(message: string, type: ToastType = 'info', duration = 5000) {
    const id = nextId++;
    const toast: ToastItem = { id, message, type, dismissing: false };

    // If we already have MAX_VISIBLE toasts, dismiss the oldest
    while (this.toasts.filter(t => !t.dismissing).length >= MAX_VISIBLE) {
      const oldest = this.toasts.find(t => !t.dismissing);
      if (oldest) this.dismiss(oldest.id);
    }

    this.toasts = [...this.toasts, toast];

    // Auto-dismiss after duration
    setTimeout(() => {
      this.dismiss(id);
    }, duration);
  }

  dismiss(id: number) {
    const toast = this.toasts.find(t => t.id === id);
    if (!toast || toast.dismissing) return;

    // Start exit animation
    toast.dismissing = true;
    this.toasts = [...this.toasts];

    // Remove after animation completes (300ms)
    setTimeout(() => {
      this.toasts = this.toasts.filter(t => t.id !== id);
    }, 300);
  }

  success(message: string, duration = 5000) {
    this.show(message, 'success', duration);
  }

  error(message: string, duration = 5000) {
    this.show(message, 'error', duration);
  }

  warning(message: string, duration = 5000) {
    this.show(message, 'warning', duration);
  }

  info(message: string, duration = 5000) {
    this.show(message, 'info', duration);
  }
}

export const toast = new ToastStore();

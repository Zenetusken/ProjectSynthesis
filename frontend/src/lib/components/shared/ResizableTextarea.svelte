<script lang="ts">
  /**
   * ResizableTextarea — shared textarea with custom drag-resize.
   *
   * Drag rule: UP = expand, DOWN = shrink. Always. Every consumer.
   * Handle is always above the textarea.
   */

  let {
    value = $bindable(''),
    placeholder = '',
    disabled = false,
    rows = 2,
    resize = 'none',
    minHeight,
    maxHeight,
    mono = false,
    fontSize = 'text-[11px]',
    onsubmit,
    class: extraClass = '',
    testid,
    ariaLabel,
  }: {
    value?: string;
    placeholder?: string;
    disabled?: boolean;
    rows?: number;
    resize?: 'none' | 'drag';
    minHeight?: number;
    maxHeight?: number;
    mono?: boolean;
    fontSize?: string;
    onsubmit?: () => void;
    class?: string;
    testid?: string;
    ariaLabel?: string;
  } = $props();

  let dragHeight = $state(minHeight ?? 56);

  function startDragResize(e: MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    const startY = e.clientY;
    const startH = dragHeight;

    const onMove = (ev: MouseEvent) => {
      // UP = expand. Mouse moves up = ev.clientY < startY = negative delta.
      // Negate so UP gives positive growth.
      const delta = startY - ev.clientY;
      dragHeight = Math.max(
        minHeight ?? 40,
        Math.min(maxHeight ?? 300, startH + delta),
      );
    };

    const onUp = () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      document.body.style.removeProperty('cursor');
      document.body.style.removeProperty('user-select');
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    document.body.style.cursor = 'row-resize';
    document.body.style.userSelect = 'none';
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      onsubmit?.();
    }
  }

  let textareaClass = $derived(
    [
      'w-full bg-bg-input border border-border-subtle text-text-primary',
      'placeholder:text-text-dim focus:outline-none focus:border-neon-cyan/40',
      'transition-colors px-2 py-1.5 resize-none',
      mono ? 'font-mono' : 'font-sans',
      fontSize,
      extraClass,
    ].filter(Boolean).join(' ')
  );

  let textareaStyle = $derived(
    resize === 'drag' ? `height: ${dragHeight}px;` : ''
  );
</script>

{#if resize === 'drag'}
  <div>
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="h-2.5 cursor-row-resize flex items-center justify-center select-none drag-handle"
      onmousedown={startDragResize}
      role="separator"
      aria-orientation="horizontal"
      aria-label="Drag to resize"
    >
      <div class="w-8 h-px bg-text-dim/20 drag-grip"></div>
    </div>
    <textarea
      class={textareaClass}
      style={textareaStyle}
      {placeholder}
      {disabled}
      {rows}
      bind:value
      onkeydown={handleKeydown}
      data-testid={testid}
      aria-label={ariaLabel}
    ></textarea>
  </div>
{:else}
  <textarea
    class={textareaClass}
    {placeholder}
    {disabled}
    {rows}
    bind:value
    onkeydown={handleKeydown}
    data-testid={testid}
    aria-label={ariaLabel}
  ></textarea>
{/if}

<style>
  .drag-handle:hover .drag-grip {
    background-color: rgba(0, 229, 255, 0.4);
  }
  .drag-handle:active .drag-grip {
    background-color: rgba(0, 229, 255, 0.6);
  }
</style>

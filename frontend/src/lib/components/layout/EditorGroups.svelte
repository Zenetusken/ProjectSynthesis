<script lang="ts">
  import { editor } from '$lib/stores/editor.svelte';
  import HelixMark from '$lib/components/shared/HelixMark.svelte';
  import PromptDocument from '$lib/components/editor/PromptDocument.svelte';
  import ForgeArtifact from '$lib/components/editor/ForgeArtifact.svelte';
  import ChainComposer from '$lib/components/editor/ChainComposer.svelte';
  import WelcomeTab from '$lib/components/editor/WelcomeTab.svelte';
  import StrategyExplainer from '$lib/components/editor/StrategyExplainer.svelte';
  import { workbench } from '$lib/stores/workbench.svelte';

  let tabBarEl = $state<HTMLElement | null>(null);

  // ── Drag-to-reorder state ─────────────────────────────────────────
  let dragging = $state(false);
  let dragIdx = $state(-1);
  let dropIdx = $state(-1);
  let dragOffsetX = $state(0);
  let dragStartX = 0;
  let dragTabW = 0;
  const DRAG_DEAD_ZONE = 3; // px before drag activates
  let dragPending = false;

  function handleDragStart(e: MouseEvent, index: number) {
    if (e.button !== 0) return;
    if ((e.target as HTMLElement).closest('button')) return; // close btn
    e.preventDefault();

    dragPending = true;
    dragIdx = index;
    dropIdx = index;
    dragStartX = e.clientX;
    dragOffsetX = 0;

    const tabEl = e.currentTarget as HTMLElement;
    dragTabW = tabEl.offsetWidth;

    const onMove = (ev: MouseEvent) => {
      const offset = ev.clientX - dragStartX;
      // Dead zone: don't activate drag until moved 3px
      if (!dragging && Math.abs(offset) < DRAG_DEAD_ZONE) return;
      if (!dragging) {
        dragging = true;
        document.body.style.cursor = 'grabbing';
        document.body.style.userSelect = 'none';
      }
      dragOffsetX = offset;

      // Calculate drop index from tab midpoints
      if (!tabBarEl) return;
      const tabEls = Array.from(tabBarEl.querySelectorAll('[data-tab-id]')) as HTMLElement[];
      let newDrop = dragIdx;
      for (let i = 0; i < tabEls.length; i++) {
        if (i === dragIdx) continue;
        const rect = tabEls[i].getBoundingClientRect();
        const midX = rect.left + rect.width / 2;
        if (dragIdx < i && ev.clientX > midX) newDrop = i;
        else if (dragIdx > i && ev.clientX < midX) newDrop = i;
      }
      dropIdx = newDrop;

      // Auto-scroll tab bar when dragging near edges
      if (tabBarEl) {
        const barRect = tabBarEl.getBoundingClientRect();
        if (ev.clientX - barRect.left < 40) tabBarEl.scrollLeft -= 8;
        else if (barRect.right - ev.clientX < 40) tabBarEl.scrollLeft += 8;
      }
    };

    const onUp = () => {
      if (dragging && dragIdx !== dropIdx) {
        editor.moveTab(dragIdx, dropIdx);
      }
      // If we never actually dragged, treat as click
      if (!dragging && dragPending) {
        editor.activeTabId = editor.openTabs[index]?.id ?? null;
      }
      dragging = false;
      dragPending = false;
      dragIdx = -1;
      dropIdx = -1;
      dragOffsetX = 0;
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }

  function getShift(i: number): number {
    if (!dragging || i === dragIdx) return 0;
    if (dragIdx < dropIdx && i > dragIdx && i <= dropIdx) return -dragTabW;
    if (dragIdx > dropIdx && i >= dropIdx && i < dragIdx) return dragTabW;
    return 0;
  }

  // ── Scroll active tab into view ───────────────────────────────────
  $effect(() => {
    const id = editor.activeTabId;
    if (!id || !tabBarEl || dragging) return;
    const el = tabBarEl.querySelector(`[data-tab-id="${id}"]`) as HTMLElement;
    el?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
  });

  // ── Handlers ──────────────────────────────────────────────────────
  function handleNewTab() {
    const id = `prompt-${Date.now()}`;
    editor.openTab({
      id,
      label: 'New Prompt',
      type: 'prompt',
      promptText: '',
      dirty: false
    });
  }

  function handleTabKeydown(e: KeyboardEvent, tabIndex: number) {
    const tabs = editor.openTabs;
    if (!tabs.length) return;
    let newIndex = tabIndex;
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault();
      newIndex = (tabIndex + 1) % tabs.length;
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault();
      newIndex = (tabIndex - 1 + tabs.length) % tabs.length;
    } else if (e.key === 'Home') {
      e.preventDefault();
      newIndex = 0;
    } else if (e.key === 'End') {
      e.preventDefault();
      newIndex = tabs.length - 1;
    } else {
      return;
    }
    editor.activeTabId = tabs[newIndex].id;
    const tabEl = document.querySelector(`[data-tab-id="${tabs[newIndex].id}"]`) as HTMLElement;
    tabEl?.focus();
  }
</script>

<main class="flex flex-col h-full overflow-hidden bg-bg-primary" aria-label="Editor">
  <!-- Tab bar — horizontal scroll, drag-to-reorder -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    bind:this={tabBarEl}
    class="h-8 flex items-center border-b border-border-subtle bg-bg-secondary shrink-0 overflow-x-auto tabbar-scroll relative"
    role="tablist"
    aria-label="Open documents"
    onwheel={(e) => {
      if (tabBarEl) { e.preventDefault(); tabBarEl.scrollLeft += e.deltaY; }
    }}
  >
    {#each editor.openTabs as tab, i (tab.id)}
      <div
        class="flex items-center gap-1 px-2 h-full text-[11px] border-r border-border-subtle whitespace-nowrap select-none shrink-0
          {editor.activeTabId === tab.id
            ? 'bg-bg-primary text-text-primary border-b border-b-neon-cyan'
            : 'text-text-dim hover:text-text-secondary hover:bg-bg-hover'}
          {dragging && i !== dragIdx ? 'transition-transform duration-150' : ''}"
        style="{dragging && i === dragIdx
          ? `transform: translateX(${dragOffsetX}px); position: relative; z-index: 10; opacity: 0.85;`
          : dragging
            ? `transform: translateX(${getShift(i)}px);`
            : ''}"
        title={tab.label}
        role="tab"
        aria-selected={editor.activeTabId === tab.id}
        tabindex={editor.activeTabId === tab.id ? 0 : -1}
        data-tab-id={tab.id}
        onmousedown={(e) => handleDragStart(e, i)}
        onkeydown={(e) => handleTabKeydown(e, i)}
      >
        <!-- Tab type icon -->
        {#if tab.type === 'prompt'}
          <svg class="w-3 h-3 shrink-0 {editor.activeTabId === tab.id ? 'opacity-100' : 'opacity-50'}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
        {:else if tab.type === 'artifact'}
          <svg class="w-3 h-3 shrink-0 {editor.activeTabId === tab.id ? 'opacity-100' : 'opacity-50'}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"></path>
          </svg>
        {:else if tab.type === 'chain'}
          <svg class="w-3 h-3 shrink-0 {editor.activeTabId === tab.id ? 'opacity-100' : 'opacity-50'}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
          </svg>
        {/if}
        {#if tab.dirty}
          <span class="w-1.5 h-1.5 rounded-full bg-neon-yellow shrink-0" title="Unsaved changes"></span>
        {/if}
        <span class="max-w-[80px] truncate">{tab.label}</span>
        <button
          class="ml-0.5 w-4 h-4 flex items-center justify-center hover:bg-bg-hover text-text-dim hover:text-text-secondary shrink-0"
          onclick={(e) => { e.stopPropagation(); editor.closeTab(tab.id); }}
          aria-label="Close tab"
          tabindex={-1}
        >
          <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
    {/each}

    <!-- New tab button -->
    <button
      class="w-7 h-full flex items-center justify-center text-text-dim hover:text-text-secondary hover:bg-bg-hover shrink-0"
      onclick={handleNewTab}
      aria-label="New tab"
    >
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"></path>
      </svg>
    </button>
  </div>

  <!-- Document area -->
  <div class="flex-1 min-h-0 overflow-y-auto" data-tour="editor" style="overscroll-behavior: contain;" role="tabpanel" aria-label={editor.activeTab ? editor.activeTab.label : 'No document open'}>
    {#if editor.activeTab}
      {#if editor.activeTab.id === 'welcome' && !editor.activeTab.promptText}
        <WelcomeTab tab={editor.activeTab} />
      {:else if editor.activeTab.type === 'strategy-ref'}
        <StrategyExplainer />
      {:else if editor.activeTab.type === 'prompt'}
        <PromptDocument tab={editor.activeTab} />
      {:else if editor.activeTab.type === 'artifact'}
        <ForgeArtifact />
      {:else if editor.activeTab.type === 'chain'}
        <ChainComposer />
      {/if}
    {:else}
      <div class="flex flex-col items-center justify-center h-full gap-3 animate-fade-in select-none">
        <HelixMark size={56} instanceId={8} speed={-0.15} opacity={0.10} />
        <span class="text-[12px] text-text-dim">No prompt open</span>
        <span class="text-[11px] text-text-dim/60">
          Press <kbd>Ctrl+N</kbd> to create a new prompt
        </span>
        <div class="flex items-center gap-2 mt-1">
          <button class="btn-outline-cyan px-3 py-1.5 text-xs" onclick={handleNewTab}>
            New Prompt
          </button>
          <button
            class="px-3 py-1.5 text-xs border border-border-subtle text-text-dim hover:border-neon-cyan/30 hover:text-text-secondary transition-colors font-mono"
            onclick={() => editor.openTab({ id: 'welcome', label: 'Welcome', type: 'prompt', promptText: '', dirty: false })}
          >Open Welcome Guide</button>
          <button
            class="px-3 py-1.5 text-xs border border-border-subtle text-text-dim hover:border-neon-cyan/30 hover:text-text-secondary transition-colors font-mono"
            onclick={() => workbench.setActivity('templates')}
          >Browse Templates</button>
        </div>
      </div>
    {/if}
  </div>
</main>

<style>
  .tabbar-scroll::-webkit-scrollbar {
    display: none;
  }
  .tabbar-scroll {
    scrollbar-width: none;
    -ms-overflow-style: none;
  }
</style>

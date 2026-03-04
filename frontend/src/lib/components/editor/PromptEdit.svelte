<script lang="ts">
  import { editor, type EditorTab } from '$lib/stores/editor.svelte';
  import { forge } from '$lib/stores/forge.svelte';
  import { startOptimization, type SSEEvent } from '$lib/api/client';
  import ContextBar from './ContextBar.svelte';
  import CopyButton from '$lib/components/shared/CopyButton.svelte';
  import ModelBadge from '$lib/components/shared/ModelBadge.svelte';
  import StrategyBadge from '$lib/components/shared/StrategyBadge.svelte';

  let { tab }: { tab: EditorTab } = $props();

  let strategy = $state('auto');
  let abortController = $state<AbortController | null>(null);

  const strategies = ['auto', 'enhance', 'chain-of-thought', 'few-shot', 'structured', 'role-based'];

  function handleInput(e: Event) {
    const target = e.target as HTMLTextAreaElement;
    editor.updateTabPrompt(tab.id, target.value);
  }

  async function handleForge() {
    if (!tab.promptText?.trim()) return;
    if (forge.isForging) return;

    forge.startForge();
    editor.setSubTab('pipeline');

    const controller = await startOptimization(
      tab.promptText,
      { strategy: strategy === 'auto' ? undefined : strategy },
      (event: SSEEvent) => {
        const data = event.data as Record<string, unknown>;
        switch (event.event) {
          case 'stage_start':
            forge.setStageRunning(data.stage as string);
            break;
          case 'stage_complete':
            forge.setStageComplete(data.stage as string, {
              stage: data.stage as string,
              data: (data.result || data) as Record<string, unknown>,
              duration: data.duration_ms as number | undefined
            });
            break;
          case 'stage_error':
            forge.setStageFailed(data.stage as string, data.error as string);
            break;
          case 'stream_chunk':
            forge.appendStreamingText(data.chunk as string || data.text as string || '');
            break;
          case 'complete':
            forge.finishForge(data.overall_score as number | undefined);
            break;
          default:
            break;
        }
      },
      (err: Error) => {
        forge.error = err.message;
        forge.isForging = false;
      },
      () => {
        if (forge.isForging) {
          forge.finishForge();
        }
      }
    );

    abortController = controller;
  }

  function handleCancel() {
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
    forge.isForging = false;
  }
</script>

<div class="flex flex-col h-full">
  <!-- Context bar -->
  <ContextBar />

  <!-- Textarea -->
  <div class="flex-1 p-4">
    <textarea
      class="w-full h-full bg-transparent text-text-primary text-sm font-mono leading-relaxed resize-none focus:outline-none placeholder:text-text-dim/50"
      placeholder="Enter your prompt here... Describe what you want the AI to do, and PromptForge will optimize it for better results."
      value={tab.promptText || ''}
      oninput={handleInput}
      spellcheck="false"
    ></textarea>
  </div>

  <!-- Action row -->
  <div class="flex items-center justify-between px-4 py-2 border-t border-border-subtle bg-bg-secondary/30 shrink-0">
    <div class="flex items-center gap-2">
      <!-- Strategy selector -->
      <select
        class="bg-bg-input border border-border-subtle rounded px-2 py-1 text-xs text-text-primary focus:outline-none focus:border-neon-cyan/30 cursor-pointer"
        bind:value={strategy}
      >
        {#each strategies as s}
          <option value={s} class="bg-bg-card">{s === 'auto' ? 'Auto Strategy' : s}</option>
        {/each}
      </select>

      <StrategyBadge strategy={strategy} />

      {#if tab.promptText}
        <CopyButton text={tab.promptText} />
      {/if}
    </div>

    <div class="flex items-center gap-2">
      {#if forge.isForging}
        <button
          class="px-3 py-1.5 rounded-lg text-xs font-medium bg-neon-red/10 text-neon-red border border-neon-red/20 hover:bg-neon-red/20 transition-all"
          onclick={handleCancel}
        >
          Cancel
        </button>
      {/if}

      <button
        class="px-4 py-1.5 rounded-lg text-xs font-semibold transition-all
          {forge.isForging
            ? 'bg-bg-card text-text-dim cursor-not-allowed'
            : 'text-white hover:shadow-lg hover:shadow-neon-cyan/20 active:scale-[0.98]'}"
        style={!forge.isForging ? 'background-image: var(--gradient-forge)' : ''}
        class:animate-forge-spark={forge.isForging}
        onclick={handleForge}
        disabled={forge.isForging || !tab.promptText?.trim()}
      >
        {forge.isForging ? 'Forging...' : 'Forge'}
      </button>
    </div>
  </div>
</div>

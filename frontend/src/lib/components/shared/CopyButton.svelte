<script lang="ts">
  import { copyToClipboard } from '$lib/utils/clipboard';

  let { text }: { text: string } = $props();

  let copied = $state(false);

  async function handleCopy() {
    const success = await copyToClipboard(text);
    if (success) {
      copied = true;
      setTimeout(() => { copied = false; }, 2000);
    }
  }
</script>

<button
  class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] transition-all
    {copied
      ? 'text-neon-green bg-neon-green/10 border border-neon-green/20'
      : 'text-text-dim hover:text-text-secondary hover:bg-bg-hover border border-transparent'}"
  class:animate-copy-flash={copied}
  onclick={handleCopy}
  aria-label="Copy to clipboard"
>
  {#if copied}
    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"></path>
    </svg>
    <span>Copied</span>
  {:else}
    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
    </svg>
    <span>Copy</span>
  {/if}
</button>

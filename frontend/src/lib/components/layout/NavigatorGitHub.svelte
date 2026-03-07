<script lang="ts">
  import { github } from '$lib/stores/github.svelte';
  import { workbench } from '$lib/stores/workbench.svelte';
  import { connectGitHub, disconnectGitHub, linkRepo, unlinkRepo, fetchLinkedRepo, getGitHubLoginUrl } from '$lib/api/client';
  import type { RepoInfo } from '$lib/api/client';
  import GitHubStatus from '$lib/components/github/GitHubStatus.svelte';
  import RepoPickerModal from '$lib/components/github/RepoPickerModal.svelte';

  let patInput = $state('');
  let connecting = $state(false);
  let showRepoPicker = $state(false);
  let showPat = $state(false);

  async function handleConnect() {
    if (!patInput.trim()) return;
    connecting = true;
    try {
      const res = await connectGitHub(patInput);
      github.setConnected(
        res.username,
        res.repos.map((r: RepoInfo) => ({
          full_name: r.full_name as string,
          description: (r.description || '') as string,
          default_branch: (r.default_branch || 'main') as string,
          private: !!r.private,
          language: r.language as string | undefined,
          size_kb: r.size_kb as number | undefined,
        }))
      );
      patInput = '';
      // Restore previously linked repo selection (non-blocking)
      fetchLinkedRepo()
        .then((linked) => {
          if (linked && linked.full_name) {
            github.selectRepo(linked.full_name, linked.branch);
          }
        })
        .catch(() => {});
    } catch (err) {
      github.setError((err as Error).message);
    } finally {
      connecting = false;
    }
  }

  function handleSelectRepo(fullName: string, branch?: string) {
    const repo = github.repos.find(r => r.full_name === fullName);
    const resolvedBranch = branch ?? repo?.default_branch;
    github.selectRepo(fullName, resolvedBranch);
    // Persist repo link to backend (non-blocking — local state already updated)
    linkRepo(fullName, resolvedBranch).catch(() => {
      // Link failed — local selection still works, just won't persist across refresh
    });
  }

  async function handleDisconnect() {
    try {
      await disconnectGitHub();
      await unlinkRepo().catch(() => {});
    } catch {
      // ignore
    }
    github.disconnect();
  }
</script>

<div class="p-2 space-y-3">
  <GitHubStatus />

  {#if !github.isConnected}
    <div class="space-y-2">
      <label class="text-xs text-text-secondary block" for="github-pat-input">
        Personal Access Token
      </label>
      <div class="relative">
        <input
          id="github-pat-input"
          type={showPat ? 'text' : 'password'}
          placeholder="ghp_..."
          class="w-full bg-bg-input border border-border-subtle rounded px-2 py-1.5 pr-8 text-xs text-text-primary placeholder:text-text-dim focus:outline-none focus:border-neon-cyan/30 font-mono"
          bind:value={patInput}
          onkeydown={(e) => { if (e.key === 'Enter') handleConnect(); }}
        />
        <button
          type="button"
          class="absolute right-1.5 top-1/2 -translate-y-1/2 text-text-dim hover:text-text-secondary transition-colors"
          onclick={() => { showPat = !showPat; }}
          aria-label={showPat ? 'Hide token' : 'Show token'}
          tabindex={-1}
        >
          {#if showPat}
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"></path>
            </svg>
          {:else}
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
            </svg>
          {/if}
        </button>
      </div>
      <button
        class="w-full py-1.5 rounded text-xs font-medium transition-all
          {connecting
            ? 'bg-bg-card text-text-dim cursor-wait'
            : 'bg-bg-card border border-border-subtle text-text-primary hover:bg-bg-hover hover:border-neon-cyan/20'}"
        onclick={handleConnect}
        disabled={connecting || !patInput.trim()}
      >
        {connecting ? 'Connecting...' : 'Connect'}
      </button>
      {#if workbench.githubOAuthEnabled}
        <div class="flex items-center gap-2 my-1">
          <div class="h-px flex-1 bg-border-subtle"></div>
          <span class="text-[10px] text-text-dim">or</span>
          <div class="h-px flex-1 bg-border-subtle"></div>
        </div>
        <button
          class="w-full py-1.5 rounded text-xs font-medium transition-all
            bg-bg-card border border-border-subtle text-text-primary
            hover:bg-bg-hover hover:border-neon-cyan/20"
          onclick={() => { window.location.href = getGitHubLoginUrl(); }}
        >
          Connect via GitHub OAuth
        </button>
      {/if}
    </div>
  {:else}
    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <span class="font-display text-[11px] font-bold uppercase text-text-dim">Repositories</span>
        <div class="flex items-center gap-2">
          <button
            class="text-[10px] text-neon-cyan hover:text-neon-cyan/80"
            onclick={() => { showRepoPicker = true; }}
          >
            Browse…
          </button>
          <button
            class="text-[10px] text-neon-red hover:text-neon-red/80"
            onclick={handleDisconnect}
          >
            Disconnect
          </button>
        </div>
      </div>

      {#each github.repos as repo}
        <button
          class="w-full text-left px-2 py-1.5 rounded text-xs transition-colors relative
            {github.selectedRepo === repo.full_name
              ? 'bg-neon-cyan/5 border border-neon-cyan/25 text-text-primary pl-3'
              : 'hover:bg-bg-hover text-text-secondary border border-transparent'}"
          onclick={() => handleSelectRepo(repo.full_name)}
        >
          {#if github.selectedRepo === repo.full_name}
            <span class="absolute left-0 top-1.5 bottom-1.5 w-[1px] bg-neon-cyan/50"></span>
          {/if}
          <div class="flex items-center gap-1.5 min-w-0">
            {#if repo.private}
              <svg class="w-3 h-3 text-neon-yellow shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"></path>
              </svg>
            {:else}
              <svg class="w-3 h-3 text-text-dim shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
              </svg>
            {/if}
            <span class="truncate">{repo.full_name}</span>
            {#if github.selectedRepo === repo.full_name && github.selectedBranch}
              <span class="text-[10px] font-mono text-neon-cyan/70 shrink-0">@ {github.selectedBranch}</span>
            {/if}
          </div>
          {#if repo.description}
            <p class="text-[10px] text-text-dim mt-0.5 truncate">{repo.description}</p>
          {/if}
        </button>
      {/each}

      {#if github.repos.length === 0}
        <p class="text-xs text-text-dim text-center py-4">No repositories found</p>
      {/if}
    </div>
  {/if}

  {#if github.error}
    <div class="text-xs text-neon-red bg-neon-red/10 px-2 py-1.5 rounded border border-neon-red/20">
      {github.error}
    </div>
  {/if}
</div>

<RepoPickerModal open={showRepoPicker} onclose={() => { showRepoPicker = false; }} onselectrepo={handleSelectRepo} />

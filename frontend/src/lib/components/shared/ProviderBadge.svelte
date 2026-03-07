<script lang="ts">
  let { provider, isConnected = true }: { provider: string; isConnected?: boolean } = $props();

  type ProviderConfig = { label: string; color: string; dotClass: string };

  const providerConfig: Record<string, ProviderConfig> = {
    anthropic:    { label: 'CLI', color: 'bg-neon-green/10 text-neon-green border-neon-green/20',   dotClass: 'bg-neon-green' },
    claude_cli:   { label: 'CLI', color: 'bg-neon-green/10 text-neon-green border-neon-green/20',   dotClass: 'bg-neon-green' },
    openai:       { label: 'API', color: 'bg-neon-yellow/10 text-neon-yellow border-neon-yellow/20', dotClass: 'bg-neon-yellow' },
    anthropic_api:{ label: 'API', color: 'bg-neon-yellow/10 text-neon-yellow border-neon-yellow/20', dotClass: 'bg-neon-yellow' },
  };

  const offlineCfg: ProviderConfig = { label: 'Offline', color: 'bg-neon-red/10 text-neon-red border-neon-red/20', dotClass: 'bg-neon-red' };
  const fallback:   ProviderConfig = { label: 'Unknown', color: 'bg-neon-red/10 text-neon-red border-neon-red/20', dotClass: 'bg-neon-red' };

  let cfg = $derived(!isConnected ? offlineCfg : (providerConfig[provider] ?? fallback));
</script>

<span
  class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-mono font-medium border {cfg.color}"
  title="Provider: {cfg.label}"
  data-testid="provider-badge"
>
  {cfg.label}
  <span class="w-1.5 h-1.5 rounded-full {cfg.dotClass} shrink-0"></span>
</span>

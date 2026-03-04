export type StageStatus = 'idle' | 'running' | 'done' | 'error' | 'skipped';

export interface StageResult {
  stage: string;
  data: Record<string, unknown>;
  duration?: number;
}

export interface PipelineEvent {
  type: string;
  stage?: string;
  data?: unknown;
  timestamp: number;
}

class ForgeStore {
  isForging = $state(false);
  currentStage = $state<string | null>(null);
  stageStatuses = $state<Record<string, StageStatus>>({
    explore: 'idle',
    analyze: 'idle',
    strategize: 'idle',
    optimize: 'idle',
    validate: 'idle'
  });
  stageResults = $state<Record<string, StageResult>>({});
  streamingText = $state('');
  overallScore = $state<number | null>(null);
  pipelineEvents = $state<PipelineEvent[]>([]);
  error = $state<string | null>(null);

  get stages() {
    return ['explore', 'analyze', 'strategize', 'optimize', 'validate'];
  }

  get completedStages(): number {
    return Object.values(this.stageStatuses).filter(s => s === 'done').length;
  }

  resetPipeline() {
    this.isForging = false;
    this.currentStage = null;
    this.stageStatuses = {
      explore: 'idle',
      analyze: 'idle',
      strategize: 'idle',
      optimize: 'idle',
      validate: 'idle'
    };
    this.stageResults = {};
    this.streamingText = '';
    this.overallScore = null;
    this.pipelineEvents = [];
    this.error = null;
  }

  startForge() {
    this.resetPipeline();
    this.isForging = true;
  }

  setStageRunning(stage: string) {
    this.currentStage = stage;
    this.stageStatuses[stage] = 'running';
    this.addEvent({ type: 'stage_start', stage, timestamp: Date.now() });
  }

  setStageComplete(stage: string, result?: StageResult) {
    this.stageStatuses[stage] = 'done';
    if (result) {
      this.stageResults[stage] = result;
    }
    this.addEvent({ type: 'stage_complete', stage, timestamp: Date.now() });
  }

  setStageFailed(stage: string, error?: string) {
    this.stageStatuses[stage] = 'error';
    this.error = error || `Stage ${stage} failed`;
    this.addEvent({ type: 'stage_error', stage, data: { error }, timestamp: Date.now() });
  }

  appendStreamingText(chunk: string) {
    this.streamingText += chunk;
  }

  finishForge(score?: number) {
    this.isForging = false;
    this.currentStage = null;
    if (score != null) {
      this.overallScore = score;
    }
    this.addEvent({ type: 'forge_complete', timestamp: Date.now() });
  }

  private addEvent(event: PipelineEvent) {
    this.pipelineEvents = [...this.pipelineEvents, event];
  }
}

export const forge = new ForgeStore();

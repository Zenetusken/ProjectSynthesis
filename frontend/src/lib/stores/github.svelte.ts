export interface GitHubRepo {
  full_name: string;
  description: string;
  default_branch: string;
  private: boolean;
}

export interface GitHubFile {
  path: string;
  sha: string;
  content?: string;
}

class GitHubStore {
  isConnected = $state(false);
  username = $state('');
  pat = $state('');
  repos = $state<GitHubRepo[]>([]);
  selectedRepo = $state<string | null>(null);
  isLoadingRepos = $state(false);
  files = $state<GitHubFile[]>([]);
  error = $state<string | null>(null);

  get currentRepo(): GitHubRepo | undefined {
    return this.repos.find(r => r.full_name === this.selectedRepo);
  }

  setPat(pat: string) {
    this.pat = pat;
  }

  setConnected(username: string, repos: GitHubRepo[]) {
    this.isConnected = true;
    this.username = username;
    this.repos = repos;
    this.error = null;
  }

  disconnect() {
    this.isConnected = false;
    this.username = '';
    this.pat = '';
    this.repos = [];
    this.selectedRepo = null;
    this.files = [];
    this.error = null;
  }

  selectRepo(fullName: string) {
    this.selectedRepo = fullName;
    this.files = [];
  }

  setFiles(files: GitHubFile[]) {
    this.files = files;
  }

  setError(error: string) {
    this.error = error;
  }
}

export const github = new GitHubStore();

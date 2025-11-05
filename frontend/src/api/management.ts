// Management API helpers for Team Lead Management page

const API_BASE_URL = 'http://localhost:8000';

export interface AnalyzeRepoPayload {
  repo_url: string;
  max_commits?: number;
}

export interface AnalyzeLocalPayload {
  local_path: string;
  max_commits?: number;
}

export async function analyzeRepo(payload: AnalyzeRepoPayload) {
  const res = await fetch(`${API_BASE_URL}/api/management/analyze-repo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ max_commits: 100, ...payload }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function analyzeLocal(payload: AnalyzeLocalPayload) {
  const res = await fetch(`${API_BASE_URL}/api/management/analyze-local`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ max_commits: 100, ...payload }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getCommits(repoName: string, limit = 50) {
  const res = await fetch(`${API_BASE_URL}/api/management/../commits?repo_name=${encodeURIComponent(repoName)}&limit=${limit}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getDevelopers(repoName: string) {
  const res = await fetch(`${API_BASE_URL}/api/management/../developers?repo_name=${encodeURIComponent(repoName)}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getCommitsByDeveloper(repoName: string, author: string, limit = 20) {
  const res = await fetch(`${API_BASE_URL}/api/management/../commits/by-developer?repo_name=${encodeURIComponent(repoName)}&author=${encodeURIComponent(author)}&limit=${limit}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function askRepo(question: string, repoName?: string, localPath?: string) {
  const res = await fetch(`${API_BASE_URL}/api/management/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, repo_name: repoName, local_path: localPath }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listCached() {
  const res = await fetch(`${API_BASE_URL}/api/management/cached`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}



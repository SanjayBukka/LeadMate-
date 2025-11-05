import React, { useMemo, useState } from 'react';
import { Navbar } from '../../components/Navbar';
import { Sidebar } from '../../components/Sidebar';
import { RefreshCw, FolderSearch, FileText, ListChecks, GitBranch, Plus } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

interface LocalAnalysisData {
  repo_name: string;
  file_analysis: Record<string, number>;
  dependencies: string[];
  key_files: Record<string, string>;
  analysis_date?: string;
  ai_summary?: string;
}

export function Management() {
  const [localPath, setLocalPath] = useState<string>(
    'C:/Users/Sanjay/Desktop/Lead Mate full Application/managemnet'
  );
  const [localName, setLocalName] = useState<string>('management-local');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<LocalAnalysisData | null>(null);
  const [repoUrl, setRepoUrl] = useState<string>('');
  const [repoName, setRepoName] = useState<string>('');
  const [repoResult, setRepoResult] = useState<any | null>(null);
  const [repoStats, setRepoStats] = useState<any | null>(null);
  const [repoDevelopers, setRepoDevelopers] = useState<any[]>([]);
  const [repoCommits, setRepoCommits] = useState<any[]>([]);
  const [clarity, setClarity] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'activity' | 'files' | 'developers' | 'commits' | 'clarity' | 'chat' | 'reports'>('overview');
  const [repoInsights, setRepoInsights] = useState<any | null>(null);
  const [repoClarity, setRepoClarity] = useState<any | null>(null);
  const [selectedDeveloper, setSelectedDeveloper] = useState<string>('');
  const [chatQuestion, setChatQuestion] = useState<string>('');
  const [chatHistory, setChatHistory] = useState<Array<{ q: string; a: string }>>([]);
  const [reportType, setReportType] = useState<'Executive Summary' | 'Developer Performance' | 'Project Health' | 'Team Activity'>('Executive Summary');
  const [reportContent, setReportContent] = useState<string>('');

  // prevent linter unused warnings when certain tabs are not rendered yet
  // eslint-disable-next-line @typescript-eslint/no-unused-expressions
  void [chatQuestion, setChatQuestion, chatHistory, setChatHistory, reportType, setReportType, reportContent, setReportContent];

  const dailyCommitSeries = useMemo(() => {
    if (!repoCommits || repoCommits.length === 0) return [] as Array<{ d: string; c: number }>;
    const map: Record<string, number> = {};
    for (const c of repoCommits) {
      if (!c?.date) continue;
      const d = new Date(c.date);
      if (isNaN(d.getTime())) continue;
      const key = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate())).toISOString().slice(0, 10);
      map[key] = (map[key] || 0) + 1;
    }
    return Object.keys(map)
      .sort()
      .map((k) => ({ d: k, c: map[k] }));
  }, [repoCommits]);

  const topDevelopers = useMemo(() => {
    return [...repoDevelopers].sort((a: any, b: any) => (b.commits || 0) - (a.commits || 0)).slice(0, 10);
  }, [repoDevelopers]);

  const fileTypesEntries = useMemo(() => {
    const ft: Record<string, number> = (repoResult?.file_analysis || repoStats?.file_types) || {};
    return Object.entries(ft);
  }, [repoResult, repoStats]);

  const authorToCommits = useMemo(() => {
    const m: Record<string, any[]> = {};
    for (const c of repoCommits) {
      const a = c?.author || 'Unknown';
      if (!m[a]) m[a] = [];
      m[a].push(c);
    }
    // sort each author's commits by date desc
    for (const k of Object.keys(m)) {
      m[k].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    }
    return m;
  }, [repoCommits]);

  const generateReport = (type: typeof reportType) => {
    const totalCommits = repoStats?.total_commits || repoCommits.length || 0;
    const contributors = repoStats?.active_developers || repoDevelopers.length || 0;
    const recent30 = repoStats?.recent_commits || 0;
    const linesAdded = repoStats?.lines_added || 0;
    const linesRemoved = repoStats?.lines_removed || 0;
    const fileTypes = Object.entries((repoResult?.file_analysis || repoStats?.file_types) || {})
      .map(([k, v]) => `${k}: ${v}`)
      .join(', ');
    const topDev = repoDevelopers?.[0]?.developer || 'Unknown';

    if (type === 'Executive Summary') {
      return `Executive Summary\n\nCommits analyzed: ${totalCommits}\nContributors: ${contributors}\nRecent (30d) commits: ${recent30}\nFile types: ${fileTypes || 'n/a'}\n\nOverall, the project shows ${recent30 > 10 ? 'healthy' : recent30 > 0 ? 'moderate' : 'low'} recent activity with ${contributors} active contributor(s).`;
    }
    if (type === 'Developer Performance') {
      const lines = repoDevelopers.slice(0, 5).map((d: any) => `- ${d.developer}: commits ${d.commits}`);
      return `Developer Performance\n\nTop contributors:\n${lines.join('\n') || 'n/a'}\n\nRecent velocity: +${linesAdded} / -${linesRemoved} lines (30d).`;
    }
    if (type === 'Project Health') {
      const velocity = (recent30 / 30).toFixed(1);
      return `Project Health\n\nCommits analyzed: ${totalCommits}\nActive developers (30d): ${contributors}\nAvg commits/day: ${velocity}\nRecent lines: +${linesAdded} / -${linesRemoved}\n\nHealth: ${recent30 > 30 ? 'Strong' : recent30 > 10 ? 'Moderate' : 'Needs attention'}.`;
    }
    const top = repoDevelopers.slice(0, 5).map((d: any) => `- ${d.developer}: commits ${d.commits}`);
    return `Team Activity\n\nContributors: ${contributors}\nMost active: ${topDev}\nCommits (30d): ${recent30}\nTop contributors:\n${top.join('\n') || 'n/a'}`;
  };

  const analyzeLocal = async () => {
    if (!localPath) return;
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/workflow/analyze-repo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: `local:${localPath}`, repo_name: localName || 'local-repo', max_commits: 100 })
      });
      const data = await response.json();
      if (!response.ok || !data?.success) {
        alert(data?.message || 'Failed to analyze');
        return;
      }
      setRepoName(data.repo_name);
      setRepoResult({ file_analysis: data.file_analysis, recent_activity: data.recent_activity });
      setRepoCommits(data.commits || []);
      setRepoDevelopers((data.developer_stats || []).map((d: any) => ({ ...d, developer: d.author })));
      // basic stats derived locally
      setRepoStats({
        total_commits: (data.commits || []).length,
        active_developers: new Set((data.commits || []).map((c: any) => c.author)).size,
        recent_commits: data.recent_activity?.total_commits || 0,
        lines_added: data.recent_activity?.lines_added || 0,
        lines_removed: data.recent_activity?.lines_removed || 0,
        file_types: data.file_analysis || {}
      });
    } catch (e) {
      console.error(e);
      alert('Error analyzing local repository');
    } finally {
      setLoading(false);
    }
  };

  const analyzeRepo = async () => {
    if (!repoUrl) return;
    setLoading(true);
    setRepoResult(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/workflow/analyze-repo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl, repo_name: repoName || 'repo', max_commits: 100 })
      });
      const data = await response.json();
      if (!response.ok || !data?.success) {
        alert(data?.message || 'Failed to analyze repository');
        return;
      }
      const payload = data.data || {};
      setRepoName(payload.repo_name || repoName);
      setRepoResult({ file_analysis: payload.file_analysis, recent_activity: payload.recent_activity });
      // Also fetch details via workflow endpoints for consistency
      try {
        const [statsRes, devRes, commitsRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/workflow/repo/${payload.repo_name || repoName}/stats`),
          fetch(`${API_BASE_URL}/api/workflow/repo/${payload.repo_name || repoName}/developers`),
          fetch(`${API_BASE_URL}/api/workflow/repo/${payload.repo_name || repoName}/commits?limit=100`)
        ]);
        if (statsRes.ok) setRepoStats(await statsRes.json());
        if (devRes.ok) setRepoDevelopers(await devRes.json());
        if (commitsRes.ok) {
          const cd = await commitsRes.json();
          setRepoCommits(cd.commits || []);
        }
      } catch {}
    } catch (e) {
      console.error(e);
      alert('Error analyzing repository');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Management</h1>
              <p className="text-gray-600 dark:text-gray-300">Analyze local project code and show essentials (file types, dependencies, key files)</p>
            </div>

            {/* Quick Selects */}
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6 mb-8">
              <div className="flex flex-wrap gap-2">
                {[
                  { label: 'DocAgent', path: 'C:/Users/Sanjay/Desktop/Lead Mate full Application/backend models/DocAgent', name: 'docagent-local' },
                  { label: 'managemnet', path: 'C:/Users/Sanjay/Desktop/Lead Mate full Application/managemnet', name: 'management-local' },
                  { label: 'Team', path: 'C:/Users/Sanjay/Desktop/Lead Mate full Application/backend models/Team', name: 'team-local' },
                  { label: 'stack', path: 'C:/Users/Sanjay/Desktop/Lead Mate full Application/backend models/stack', name: 'stack-local' }
                ].map((p) => (
                  <button
                    key={p.label}
                    onClick={() => { setLocalPath(p.path); setLocalName(p.name); setRepoUrl(''); setResult(null); setRepoResult(null); }}
                    className="px-3 py-1.5 text-sm rounded-md bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600"
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {false && (
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <FolderSearch className="w-5 h-5" /> Local Directory
              </h2>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Absolute Path</label>
                  <input
                    type="text"
                    value={localPath}
                    onChange={(e) => setLocalPath(e.target.value)}
                    placeholder="C:/full/path/to/folder"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Name</label>
                  <input
                    type="text"
                    value={localName}
                    onChange={(e) => setLocalName(e.target.value)}
                    placeholder="management-local"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              </div>
              <button
                onClick={analyzeLocal}
                disabled={loading || !localPath}
                className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ListChecks className="w-4 h-4" />}
                {loading ? 'Analyzing...' : 'Analyze'}
              </button>
            </div>
            )}

            {result && (
              <div className="space-y-8">
                {result.ai_summary && (
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">AI Summary (Ollama)</h3>
                    <div className="prose dark:prose-invert max-w-none whitespace-pre-wrap text-gray-800 dark:text-gray-200">
                      {result.ai_summary}
                    </div>
                  </div>
                )}
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">File Types</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {Object.entries(result.file_analysis).map(([ext, count]) => (
                      <div key={ext} className="rounded-lg p-4 bg-gray-50 dark:bg-gray-700/50">
                        <div className="text-sm text-gray-500 dark:text-gray-400">{ext || 'no-ext'}</div>
                        <div className="text-xl font-semibold text-gray-900 dark:text-white">{count}</div>
                      </div>
                    ))}
                    {Object.keys(result.file_analysis).length === 0 && (
                      <div className="text-gray-600 dark:text-gray-300">No files found</div>
                    )}
                  </div>
                </div>

                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Dependencies</h3>
                  {result.dependencies.length > 0 ? (
                    <ul className="list-disc pl-6 space-y-1 text-gray-800 dark:text-gray-200">
                      {result.dependencies.map((dep, idx) => (
                        <li key={idx}>{dep}</li>
                      ))}
                    </ul>
                  ) : (
                    <div className="text-gray-600 dark:text-gray-300">No requirements.txt detected</div>
                  )}
                </div>

                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <FileText className="w-5 h-5" /> Key Files Preview
                  </h3>
                  {Object.keys(result.key_files || {}).length > 0 ? (
                    <div className="space-y-4">
                      {Object.entries(result.key_files).map(([name, content]) => (
                        <div key={name} className="rounded-lg border border-gray-200 dark:border-gray-700">
                          <div className="px-4 py-2 bg-gray-50 dark:bg-gray-700/50 text-sm font-medium text-gray-700 dark:text-gray-300">{name}</div>
                          <pre className="p-4 text-sm overflow-auto whitespace-pre-wrap text-gray-900 dark:text-gray-100">{content}</pre>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-gray-600 dark:text-gray-300">No key files found</div>
                  )}
                </div>
              </div>
            )}

            {/* Git Repository Analysis */}
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6 mt-12 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <GitBranch className="w-5 h-5" /> Git Repository
              </h2>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Repository URL</label>
                  <input
                    type="text"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    placeholder="https://github.com/username/repo.git or local:C:/path"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Name</label>
                  <input
                    type="text"
                    value={repoName}
                    onChange={(e) => setRepoName(e.target.value)}
                    placeholder="my-project"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              </div>
              <button
                onClick={analyzeRepo}
                disabled={loading || !repoUrl}
                className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                {loading ? 'Analyzing...' : 'Analyze Repository'}
              </button>
            </div>

            {/* Tabs - always visible */}
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-4 mb-6">
              <div className="flex flex-wrap gap-2">
                {[
                  { id: 'overview', label: 'Overview' },
                  { id: 'activity', label: 'Activity' },
                  { id: 'files', label: 'File Types' },
                  { id: 'developers', label: 'Developers' },
                  { id: 'commits', label: 'Commits' },
                  { id: 'clarity', label: 'Clarity' },
                  { id: 'chat', label: 'AI Chat' },
                  { id: 'reports', label: 'Reports' }
                ].map(t => (
                  <button
                    key={t.id}
                    onClick={() => setActiveTab(t.id as any)}
                    className={`px-3 py-1.5 rounded-md text-sm ${
                      activeTab === (t.id as any)
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white underline underline-offset-4'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-8">
              {activeTab === 'overview' && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
                    <div className="text-sm text-gray-600 dark:text-gray-300">Total Commits</div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">{repoStats?.total_commits ?? 0}</div>
                  </div>
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
                    <div className="text-sm text-gray-600 dark:text-gray-300">Contributors</div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">{repoStats?.active_developers ?? 0}</div>
                  </div>
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
                    <div className="text-sm text-gray-600 dark:text-gray-300">Lines Added</div>
                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">+{repoStats?.lines_added ?? 0}</div>
                  </div>
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
                    <div className="text-sm text-gray-600 dark:text-gray-300">30d Commits</div>
                    <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{repoStats?.recent_commits ?? 0}</div>
                  </div>
                </div>
              )}

              {activeTab === 'overview' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Commit Activity Over Time</h3>
                    <div className="flex items-end gap-1 h-32">
                      {dailyCommitSeries.length > 0 ? (
                        dailyCommitSeries.map((p, i) => {
                          const max = Math.max(...dailyCommitSeries.map(v => v.c));
                          const h = max > 0 ? Math.max(4, Math.round((p.c / max) * 100)) : 0;
                          return (
                            <div key={i} title={`${p.d}: ${p.c}`} className="bg-gradient-to-t from-blue-600 to-purple-500 rounded-t" style={{ width: '6px', height: `${h}%` }} />
                          );
                        })
                      ) : (
                        <div className="text-sm text-gray-600 dark:text-gray-300">No commits</div>
                      )}
                    </div>
                  </div>
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">File Types Distribution</h3>
                    {fileTypesEntries.length > 0 ? (
                      <div className="space-y-2">
                        {fileTypesEntries.map(([ext, count]) => {
                          const total = fileTypesEntries.reduce((s, [, c]) => s + (Number(c) || 0), 0) || 1;
                          const pct = Math.round(((Number(count) || 0) / total) * 100);
                          return (
                            <div key={ext} className="">
                              <div className="flex justify-between text-xs text-gray-600 dark:text-gray-300"><span>{ext || 'no-ext'}</span><span>{count}</span></div>
                              <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded">
                                <div className="h-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded" style={{ width: `${pct}%` }} />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="text-sm text-gray-600 dark:text-gray-300">No file data</div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'overview' && (
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Project Summary</h3>
                  {repoInsights?.project_summary ? (
                    <div className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{repoInsights.project_summary.summary || JSON.stringify(repoInsights.project_summary)}</div>
                  ) : (
                    <div className="text-sm text-gray-600 dark:text-gray-400">Analyze a repository to view AI Project Summary.</div>
                  )}
                </div>
              )}

              {activeTab === 'files' && (
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">File Types</h3>
                  {repoResult?.file_analysis || repoStats?.file_types ? (
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {Object.entries(repoResult?.file_analysis || repoStats?.file_types || {}).map(([ext, count]: any) => (
                        <div key={ext} className="rounded-lg p-4 bg-gray-50 dark:bg-gray-700/50">
                          <div className="text-sm text-gray-500 dark:text-gray-400">{ext || 'no-ext'}</div>
                          <div className="text-xl font-semibold text-gray-900 dark:text-white">{count as any}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-gray-600 dark:text-gray-400">Analyze a repository to view file type distribution.</div>
                  )}
                </div>
              )}

              {activeTab === 'developers' && (
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Top Contributors</h3>
                  {repoDevelopers?.length ? (
                    <div className="space-y-2">
                      {topDevelopers.map((dev: any) => (
                        <button key={dev.developer} onClick={() => setSelectedDeveloper(dev.developer)} className="w-full text-left">
                          <div className="flex items-center gap-4">
                            <div className="w-40 text-sm text-gray-700 dark:text-gray-300 truncate">{dev.developer}</div>
                            <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded">
                              <div className="h-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded" style={{ width: `${Math.min(100, (dev.commits || 0) * 5)}%` }} />
                            </div>
                            <div className="w-10 text-right text-sm text-gray-700 dark:text-gray-300">{dev.commits}</div>
                          </div>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-gray-600 dark:text-gray-400">Analyze a repository to view developer contributions.</div>
                  )}

                  {selectedDeveloper && (
                    <div className="mt-6 border-t border-gray-2 00 dark:border-gray-700 pt-4">
                      <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3">{selectedDeveloper} — Details</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        {(() => {
                          const dev = repoDevelopers.find((d: any) => d.developer === selectedDeveloper);
                          if (!dev) return null as any;
                          return (
                            <>
                              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                                <div className="text-xs text-gray-500 dark:text-gray-400">Commits</div>
                                <div className="text-lg font-semibold text-gray-900 dark:text-white">{dev.commits}</div>
                              </div>
                              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                                <div className="text-xs text-gray-500 dark:text-gray-400">Insertions</div>
                                <div className="text-lg font-semibold text-green-600 dark:text-green-400">+{dev.insertions || 0}</div>
                              </div>
                              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                                <div className="text-xs text-gray-500 dark:text-gray-400">Deletions</div>
                                <div className="text-lg font-semibold text-red-600 dark:text-red-400">-{dev.deletions || 0}</div>
                              </div>
                              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                                <div className="text-xs text-gray-500 dark:text-gray-400">Files Modified</div>
                                <div className="text-lg font-semibold text-gray-900 dark:text-white">{dev.files_changed || dev.files_modified || 0}</div>
                              </div>
                            </>
                          );
                        })()}
                      </div>
                      <div>
                        <h5 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Recent Commits</h5>
                        <div className="space-y-2">
                          {repoCommits.filter((c: any) => c.author === selectedDeveloper).slice(0, 10).map((c: any, idx: number) => (
                            <div key={idx} className="text-sm text-gray-800 dark:text-gray-200 flex items-center justify-between">
                              <div className="truncate pr-4">{c.message}</div>
                              <div className="text-xs text-gray-500 dark:text-gray-400">{new Date(c.date).toLocaleString()}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'activity' && (
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Commits</h3>
                  {repoCommits?.length ? (
                    <div className="space-y-3">
                      {repoCommits.slice(0, 20).map((c: any, idx: number) => (
                        <div key={idx} className="text-sm text-gray-800 dark:text-gray-200 flex items-center justify-between">
                          <div className="truncate pr-4">
                            <span className="font-medium">{c.author}</span> • {c.message}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">{new Date(c.date).toLocaleDateString()}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-gray-600 dark:text-gray-400">Analyze a repository to view recent commits.</div>
                  )}
                </div>
              )}

              {activeTab === 'commits' && (
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Developers and Their Commits</h3>
                  {Object.keys(authorToCommits).length ? (
                    <div className="space-y-6">
                      {topDevelopers.map((dev: any) => {
                        const commits = authorToCommits[dev.developer] || [];
                        return (
                          <div key={dev.developer} className="rounded-lg border border-gray-200 dark:border-gray-700">
                            <div className="px-4 py-3 bg-gray-50 dark:bg-gray-700/50 flex items-center justify-between">
                              <div className="text-sm font-medium text-gray-900 dark:text-white">{dev.developer}</div>
                              <div className="text-xs text-gray-700 dark:text-gray-300">Commits: {dev.commits}</div>
                            </div>
                            <div className="p-4 space-y-2">
                              {commits.slice(0, 5).map((c: any, idx: number) => (
                                <div key={idx} className="text-sm text-gray-800 dark:text-gray-200 flex items-center justify-between">
                                  <div className="truncate pr-4">{c.message}</div>
                                  <div className="text-xs text-gray-500 dark:text-gray-400">{new Date(c.date).toLocaleString()}</div>
                                </div>
                              ))}
                              {commits.length === 0 && (
                                <div className="text-sm text-gray-600 dark:text-gray-400">No commits available for this developer.</div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="text-sm text-gray-600 dark:text-gray-400">Analyze a repository to view developers and their commits.</div>
                  )}
                </div>
              )}

              {activeTab === 'overview' && repoInsights?.team_recommendations && repoInsights.team_recommendations.length > 0 && (
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Team Recommendations</h3>
                  <ul className="list-disc pl-6 space-y-1 text-gray-800 dark:text-gray-200">
                    {repoInsights.team_recommendations.map((r: string, idx: number) => (
                      <li key={idx}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}

              {activeTab === 'clarity' && (
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Code Clarity Agent</h3>
                    <button
                      onClick={async () => {
                        if (!repoName) return;
                        try {
                          const r = await fetch(`${API_BASE_URL}/api/workflow/repo/${repoName}/clarity`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` } });
                          if (r.ok) {
                            const d = await r.json();
                            setRepoClarity(d);
                          } else {
                            runCodeClarity();
                          }
                        } catch { runCodeClarity(); }
                      }}
                      disabled={loading}
                      className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50"
                    >
                      Analyze Clarity
                    </button>
                  </div>
                  {repoClarity ? (
                    <>
                      <div className="mb-3 text-sm text-gray-700 dark:text-gray-300">
                        Metrics: commits {repoClarity?.metrics?.total_commits ?? 0}, contributors {repoClarity?.metrics?.contributors ?? 0}, 30d commits {repoClarity?.metrics?.recent_commits_30d ?? 0}
                      </div>
                      <ul className="list-disc pl-6 space-y-1 text-gray-800 dark:text-gray-200">
                        {(repoClarity.recommendations || []).map((s: string, i: number) => <li key={i}>{s}</li>)}
                      </ul>
                    </>
                  ) : clarity.length > 0 ? (
                    <ul className="list-disc pl-6 space-y-1 text-gray-800 dark:text-gray-200">
                      {clarity.map((s, i) => (<li key={i}>{s}</li>))}
                    </ul>
                  ) : (
                    <div className="text-gray-600 dark:text-gray-300">Run the analysis to get actionable suggestions.</div>
                  )}
                </div>
              )}

              {activeTab === 'chat' && (
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">AI Chat</h3>
                  <div className="space-y-3">
                    <input
                      type="text"
                      value={chatQuestion}
                      onChange={(e) => setChatQuestion(e.target.value)}
                      placeholder="Ask about the repository..."
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          if (!chatQuestion.trim()) return;
                          const a = generateAIAnswer(chatQuestion.trim());
                          setChatHistory((h) => [...h, { q: chatQuestion.trim(), a }]);
                          setChatQuestion('');
                        }}
                        className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700"
                      >
                        Ask
                      </button>
                      <button
                        onClick={() => setChatHistory([])}
                        className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg"
                      >
                        Clear
                      </button>
                    </div>
                    <div className="space-y-4">
                      {chatHistory.map((m, i) => (
                        <div key={i} className="rounded-lg border border-gray-200 dark:border-gray-700">
                          <div className="px-4 py-2 bg-gray-50 dark:bg-gray-700/50 text-sm text-gray-700 dark:text-gray-300">You: {m.q}</div>
                          <div className="p-4 text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap">{m.a}</div>
                        </div>
                      ))}
                      {chatHistory.length === 0 && (
                        <div className="text-sm text-gray-600 dark:text-gray-300">Ask a question to get started.</div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'reports' && (
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Reports</h3>
                    <div className="flex items-center gap-2">
                      <select
                        value={reportType}
                        onChange={(e) => setReportType(e.target.value as any)}
                        className="px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-300 dark:border-gray-600 rounded-lg"
                      >
                        <option>Executive Summary</option>
                        <option>Developer Performance</option>
                        <option>Project Health</option>
                        <option>Team Activity</option>
                      </select>
                      <button
                        onClick={() => setReportContent(generateReport(reportType))}
                        className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700"
                      >
                        Generate
                      </button>
                    </div>
                  </div>
                  {reportContent ? (
                    <pre className="whitespace-pre-wrap text-sm text-gray-900 dark:text-gray-100">{reportContent}</pre>
                  ) : (
                    <div className="text-sm text-gray-600 dark:text-gray-300">Choose a report type and click Generate.</div>
                  )}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}



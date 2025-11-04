import React, { useState } from 'react';
import { Navbar } from '../../components/Navbar';
import { Sidebar } from '../../components/Sidebar';
import { RefreshCw, FolderSearch, FileText, ListChecks } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

interface LocalAnalysisData {
  repo_name: string;
  file_analysis: Record<string, number>;
  dependencies: string[];
  key_files: Record<string, string>;
  analysis_date?: string;
}

export function Management() {
  const [localPath, setLocalPath] = useState<string>(
    'C:/Users/Sanjay/Desktop/Lead Mate full Application/backend models/managemnet'
  );
  const [repoName, setRepoName] = useState<string>('management-local');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<LocalAnalysisData | null>(null);

  const analyzeLocal = async () => {
    if (!localPath || !repoName) return;
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/workflow/analyze-repo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          repo_url: `local:${localPath}`,
          repo_name: repoName
        })
      });

      const data = await response.json();
      if (!response.ok || !data?.success) {
        alert(data?.message || 'Failed to analyze');
        return;
      }
      setResult(data.data as LocalAnalysisData);
    } catch (e) {
      console.error(e);
      alert('Error analyzing local directory');
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
                    value={repoName}
                    onChange={(e) => setRepoName(e.target.value)}
                    placeholder="management-local"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              </div>
              <button
                onClick={analyzeLocal}
                disabled={loading || !localPath || !repoName}
                className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ListChecks className="w-4 h-4" />}
                {loading ? 'Analyzing...' : 'Analyze'}
              </button>
            </div>

            {result && (
              <div className="space-y-8">
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
          </div>
        </main>
      </div>
    </div>
  );
}



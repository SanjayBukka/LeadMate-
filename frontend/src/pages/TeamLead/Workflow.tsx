import React, { useState, useEffect } from 'react';
import { Navbar } from '../../components/Navbar';
import { Sidebar } from '../../components/Sidebar';
import { GitBranch, Users, Activity, TrendingUp, Clock, CheckCircle, Plus, RefreshCw, GitCommit, GitMerge, ExternalLink } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const API_BASE_URL = 'http://localhost:8000';

interface Commit {
  hash: string;
  author: string;
  message: string;
  date: string;
  files_changed: number;
  insertions: number;
  deletions: number;
}

interface RepositoryStats {
  total_commits: number;
  active_developers: number;
  lines_added: number;
  lines_removed: number;
  most_active_dev: string;
  file_types: Record<string, number>;
}

interface DeveloperInsight {
  developer: string;
  commits: number;
  lines_added: number;
  lines_removed: number;
  files_modified: number;
  activity_days: number;
  avg_changes_per_commit: number;
  insight: string;
}

export function Workflow() {
  const { user } = useAuth();
  const [repositories, setRepositories] = useState<string[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<string>('');
  const [stats, setStats] = useState<RepositoryStats | null>(null);
  const [commits, setCommits] = useState<Commit[]>([]);
  const [developers, setDevelopers] = useState<DeveloperInsight[]>([]);
  const [loading, setLoading] = useState(false);
  const [repoUrl, setRepoUrl] = useState('');
  const [repoName, setRepoName] = useState('');

  // Load cached repositories on mount
  useEffect(() => {
    fetchRepositories();
  }, []);

  // Load repository data when selected
  useEffect(() => {
    if (selectedRepo) {
      fetchRepositoryData(selectedRepo);
    }
  }, [selectedRepo]);

  const fetchRepositories = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/workflow/repos`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setRepositories(data);
      }
    } catch (error) {
      console.error('Error fetching repositories:', error);
    }
  };

  const fetchRepositoryData = async (repoName: string) => {
    setLoading(true);
    try {
      // Fetch stats
      const statsResponse = await fetch(`${API_BASE_URL}/api/workflow/repo/${repoName}/stats`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }

      // Fetch commits
      const commitsResponse = await fetch(`${API_BASE_URL}/api/workflow/repo/${repoName}/commits?limit=20`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (commitsResponse.ok) {
        const commitsData = await commitsResponse.json();
        setCommits(commitsData.commits || []);
      }

      // Fetch developer insights
      const devResponse = await fetch(`${API_BASE_URL}/api/workflow/repo/${repoName}/developers`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (devResponse.ok) {
        const devData = await devResponse.json();
        setDevelopers(devData);
      }
    } catch (error) {
      console.error('Error fetching repository data:', error);
    } finally {
      setLoading(false);
    }
  };

  const analyzeRepository = async () => {
    if (!repoUrl || !repoName) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/workflow/analyze-repo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          repo_url: repoUrl,
          repo_name: repoName
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSelectedRepo(repoName);
          fetchRepositories(); // Refresh repository list
          setRepoUrl('');
          setRepoName('');
        } else {
          alert(`Error: ${data.message}`);
        }
      } else {
        alert('Failed to analyze repository');
      }
    } catch (error) {
      console.error('Error analyzing repository:', error);
      alert('Error analyzing repository');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatTimeAgo = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900">
      <Navbar />
      
      <div className="flex">
        <Sidebar />
        
        <main className="flex-1 p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                Workflow & Git Activity
              </h1>
              <p className="text-gray-600 dark:text-gray-300">
                Monitor team development activity and code contributions
              </p>
            </div>

            {/* Repository Selection */}
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Repository Analysis
              </h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Repository URL
                  </label>
                  <input
                    type="url"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    placeholder="https://github.com/username/repository"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Repository Name
                  </label>
                  <input
                    type="text"
                    value={repoName}
                    onChange={(e) => setRepoName(e.target.value)}
                    placeholder="my-project"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              </div>
              
              <div className="flex gap-4">
                <button
                  onClick={analyzeRepository}
                  disabled={loading || !repoUrl || !repoName}
                  className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  {loading ? 'Analyzing...' : 'Analyze Repository'}
                </button>
                
                {repositories.length > 0 && (
                  <select
                    value={selectedRepo}
                    onChange={(e) => setSelectedRepo(e.target.value)}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="">Select cached repository</option>
                    {repositories.map((repo) => (
                      <option key={repo} value={repo}>{repo}</option>
                    ))}
                  </select>
                )}
              </div>
            </div>

            {loading && (
              <div className="flex items-center justify-center py-20">
                <div className="text-center">
                  <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
                  <p className="text-gray-600 dark:text-gray-300">Analyzing repository...</p>
                </div>
              </div>
            )}

            {stats && !loading && (
              <>
                {/* Statistics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-xl flex items-center justify-center">
                        <GitCommit className="w-6 h-6 text-green-600 dark:text-green-400" />
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total_commits}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-300">Total Commits</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
                        <Users className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.active_developers}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-300">Active Developers</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-xl flex items-center justify-center">
                        <TrendingUp className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">+{stats.lines_added}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-300">Lines Added</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-xl flex items-center justify-center">
                        <Activity className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.most_active_dev}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-300">Most Active</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Developer Insights */}
                {developers.length > 0 && (
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6 mb-8">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                      Developer Insights
                    </h2>
                    
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {developers.slice(0, 4).map((dev, index) => (
                        <div key={index} className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                          <div className="flex items-center justify-between mb-3">
                            <h3 className="font-semibold text-gray-900 dark:text-white">{dev.developer}</h3>
                            <span className="text-sm text-gray-600 dark:text-gray-300">{dev.commits} commits</span>
                          </div>
                          <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                            <div>
                              <span className="text-gray-600 dark:text-gray-300">Lines Added:</span>
                              <span className="ml-2 font-medium text-green-600 dark:text-green-400">+{dev.lines_added}</span>
                            </div>
                            <div>
                              <span className="text-gray-600 dark:text-gray-300">Files Modified:</span>
                              <span className="ml-2 font-medium text-blue-600 dark:text-blue-400">{dev.files_modified}</span>
                            </div>
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-300 italic">
                            {dev.insight}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recent Commits */}
                {commits.length > 0 && (
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                      Recent Commits
                    </h2>
                    
                    <div className="space-y-4">
                      {commits.slice(0, 10).map((commit, index) => (
                        <div key={index} className="flex items-start space-x-3 p-4 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                          <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                            <GitCommit className="w-4 h-4 text-white" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium text-gray-900 dark:text-white">
                                {commit.author}
                              </span>
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {formatTimeAgo(commit.date)}
                              </span>
                            </div>
                            <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                              {commit.message}
                            </p>
                            <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                              <span className="flex items-center">
                                <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                                +{commit.insertions}
                              </span>
                              <span className="flex items-center">
                                <span className="w-2 h-2 bg-red-500 rounded-full mr-1"></span>
                                -{commit.deletions}
                              </span>
                              <span>{commit.files_changed} files</span>
                              <span className="font-mono text-gray-400">{commit.hash}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {!stats && !loading && selectedRepo && (
              <div className="flex items-center justify-center py-20">
                <div className="text-center">
                  <GitBranch className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    No data available
                  </h3>
                  <p className="text-gray-600 dark:text-gray-300">
                    This repository hasn't been analyzed yet or contains no commits.
                  </p>
                </div>
              </div>
            )}

            {!selectedRepo && !loading && (
              <div className="flex items-center justify-center py-20">
                <div className="text-center">
                  <GitBranch className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    Select a repository
                  </h3>
                  <p className="text-gray-600 dark:text-gray-300">
                    Choose a repository from the dropdown or analyze a new one to view workflow data.
                  </p>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
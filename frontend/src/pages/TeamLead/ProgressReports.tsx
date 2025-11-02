import React, { useState, useEffect } from 'react';
import { Navbar } from '../../components/Navbar';
import { Sidebar } from '../../components/Sidebar';
import { FileBarChart, TrendingUp, Users, Clock, CheckCircle, AlertCircle, Target, Calendar, Download } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const API_BASE_URL = 'http://localhost:8000';

interface WeeklyReport {
  week_start: string;
  week_end: string;
  total_commits: number;
  active_developers: number;
  lines_added: number;
  lines_removed: number;
  top_contributor: string;
  key_achievements: string[];
  challenges: string[];
  next_week_goals: string[];
}

interface MonthlyReport {
  month: string;
  year: number;
  total_commits: number;
  active_developers: number;
  lines_added: number;
  lines_removed: number;
  project_velocity: number;
  team_productivity: string;
  key_milestones: string[];
  technical_debt: string;
  recommendations: string[];
}

interface TeamPerformance {
  team_size: number;
  active_members: number;
  average_commits_per_week: number;
  code_review_coverage: number;
  bug_resolution_time: string;
  feature_completion_rate: number;
  team_satisfaction: number;
  top_performers: Array<{
    name: string;
    commits: number;
    lines_added: number;
    code_quality: number;
  }>;
  improvement_areas: string[];
}

interface ProductivityTrend {
  week: string;
  commits: number;
  lines_added: number;
  lines_removed: number;
  active_developers: number;
}

export function ProgressReports() {
  const { user } = useAuth();
  const [weeklyReport, setWeeklyReport] = useState<WeeklyReport | null>(null);
  const [monthlyReport, setMonthlyReport] = useState<MonthlyReport | null>(null);
  const [teamPerformance, setTeamPerformance] = useState<TeamPerformance | null>(null);
  const [productivityTrends, setProductivityTrends] = useState<ProductivityTrend[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'weekly' | 'monthly' | 'team' | 'trends'>('weekly');

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    setLoading(true);
    try {
      // Fetch weekly report
      const weeklyResponse = await fetch(`${API_BASE_URL}/api/reports/weekly/sample-repo`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (weeklyResponse.ok) {
        const weeklyData = await weeklyResponse.json();
        setWeeklyReport(weeklyData);
      }

      // Fetch monthly report
      const monthlyResponse = await fetch(`${API_BASE_URL}/api/reports/monthly/sample-repo`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (monthlyResponse.ok) {
        const monthlyData = await monthlyResponse.json();
        setMonthlyReport(monthlyData);
      }

      // Fetch team performance
      const teamResponse = await fetch(`${API_BASE_URL}/api/reports/team-performance`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (teamResponse.ok) {
        const teamData = await teamResponse.json();
        setTeamPerformance(teamData);
      }

      // Fetch productivity trends
      const trendsResponse = await fetch(`${API_BASE_URL}/api/reports/productivity-trends`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (trendsResponse.ok) {
        const trendsData = await trendsResponse.json();
        setProductivityTrends(trendsData.trends || []);
      }
    } catch (error) {
      console.error('Error fetching reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const renderWeeklyReport = () => {
    if (!weeklyReport) return null;

    return (
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
                <FileBarChart className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{weeklyReport.total_commits}</p>
                <p className="text-sm text-gray-600 dark:text-gray-300">Commits</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-xl flex items-center justify-center">
                <Users className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{weeklyReport.active_developers}</p>
                <p className="text-sm text-gray-600 dark:text-gray-300">Active Devs</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">+{weeklyReport.lines_added}</p>
                <p className="text-sm text-gray-600 dark:text-gray-300">Lines Added</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-xl flex items-center justify-center">
                <Target className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{weeklyReport.top_contributor}</p>
                <p className="text-sm text-gray-600 dark:text-gray-300">Top Contributor</p>
              </div>
            </div>
          </div>
        </div>

        {/* Key Achievements */}
        <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
            Key Achievements
          </h3>
          <ul className="space-y-2">
            {weeklyReport.key_achievements.map((achievement, index) => (
              <li key={index} className="flex items-start">
                <span className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                <span className="text-gray-700 dark:text-gray-300">{achievement}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Challenges and Goals */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <AlertCircle className="w-5 h-5 text-yellow-600 mr-2" />
              Challenges
            </h3>
            <ul className="space-y-2">
              {weeklyReport.challenges.map((challenge, index) => (
                <li key={index} className="flex items-start">
                  <span className="w-2 h-2 bg-yellow-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                  <span className="text-gray-700 dark:text-gray-300">{challenge}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <Target className="w-5 h-5 text-blue-600 mr-2" />
              Next Week Goals
            </h3>
            <ul className="space-y-2">
              {weeklyReport.next_week_goals.map((goal, index) => (
                <li key={index} className="flex items-start">
                  <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                  <span className="text-gray-700 dark:text-gray-300">{goal}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    );
  };

  const renderMonthlyReport = () => {
    if (!monthlyReport) return null;

    return (
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
                <FileBarChart className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{monthlyReport.total_commits}</p>
                <p className="text-sm text-gray-600 dark:text-gray-300">Total Commits</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{monthlyReport.project_velocity}%</p>
                <p className="text-sm text-gray-600 dark:text-gray-300">Velocity</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-xl flex items-center justify-center">
                <Users className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{monthlyReport.active_developers}</p>
                <p className="text-sm text-gray-600 dark:text-gray-300">Active Devs</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-xl flex items-center justify-center">
                <Clock className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">+{monthlyReport.lines_added}</p>
                <p className="text-sm text-gray-600 dark:text-gray-300">Lines Added</p>
              </div>
            </div>
          </div>
        </div>

        {/* Key Milestones */}
        <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
            Key Milestones
          </h3>
          <ul className="space-y-3">
            {monthlyReport.key_milestones.map((milestone, index) => (
              <li key={index} className="flex items-start">
                <span className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                <span className="text-gray-700 dark:text-gray-300">{milestone}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Team Productivity and Recommendations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Team Productivity
            </h3>
            <p className="text-gray-700 dark:text-gray-300">{monthlyReport.team_productivity}</p>
          </div>

          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Technical Debt
            </h3>
            <p className="text-gray-700 dark:text-gray-300">{monthlyReport.technical_debt}</p>
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <Target className="w-5 h-5 text-blue-600 mr-2" />
            Recommendations
          </h3>
          <ul className="space-y-2">
            {monthlyReport.recommendations.map((recommendation, index) => (
              <li key={index} className="flex items-start">
                <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                <span className="text-gray-700 dark:text-gray-300">{recommendation}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  const renderTeamPerformance = () => {
    if (!teamPerformance) return null;

    return (
      <div className="space-y-6">
        {/* Team Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
                <Users className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{teamPerformance.team_size}</p>
                <p className="text-sm text-gray-600 dark:text-gray-300">Team Size</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-xl flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{teamPerformance.active_members}</p>
                <p className="text-sm text-gray-600 dark:text-gray-300">Active Members</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{teamPerformance.average_commits_per_week}</p>
                <p className="text-sm text-gray-600 dark:text-gray-300">Avg Commits/Week</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-xl flex items-center justify-center">
                <Target className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{teamPerformance.feature_completion_rate}%</p>
                <p className="text-sm text-gray-600 dark:text-gray-300">Completion Rate</p>
              </div>
            </div>
          </div>
        </div>

        {/* Top Performers */}
        <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            Top Performers
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {teamPerformance.top_performers.map((performer, index) => (
              <div key={index} className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-gray-900 dark:text-white">{performer.name}</h4>
                  <span className="text-sm text-gray-600 dark:text-gray-300">Quality: {performer.code_quality}%</span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600 dark:text-gray-300">Commits:</span>
                    <span className="ml-2 font-medium text-blue-600 dark:text-blue-400">{performer.commits}</span>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-300">Lines Added:</span>
                    <span className="ml-2 font-medium text-green-600 dark:text-green-400">+{performer.lines_added}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Improvement Areas */}
        <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <AlertCircle className="w-5 h-5 text-yellow-600 mr-2" />
            Improvement Areas
          </h3>
          <ul className="space-y-2">
            {teamPerformance.improvement_areas.map((area, index) => (
              <li key={index} className="flex items-start">
                <span className="w-2 h-2 bg-yellow-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                <span className="text-gray-700 dark:text-gray-300">{area}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  const renderProductivityTrends = () => {
    return (
      <div className="space-y-6">
        <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            Productivity Trends (Last 12 Weeks)
          </h3>
          <div className="space-y-4">
            {productivityTrends.map((trend, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                    <Calendar className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">Week {index + 1}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-300">{trend.week}</p>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-6 text-sm">
                  <div className="text-center">
                    <p className="font-semibold text-gray-900 dark:text-white">{trend.commits}</p>
                    <p className="text-gray-600 dark:text-gray-300">Commits</p>
                  </div>
                  <div className="text-center">
                    <p className="font-semibold text-green-600 dark:text-green-400">+{trend.lines_added}</p>
                    <p className="text-gray-600 dark:text-gray-300">Added</p>
                  </div>
                  <div className="text-center">
                    <p className="font-semibold text-red-600 dark:text-red-400">-{trend.lines_removed}</p>
                    <p className="text-gray-600 dark:text-gray-300">Removed</p>
                  </div>
                  <div className="text-center">
                    <p className="font-semibold text-gray-900 dark:text-white">{trend.active_developers}</p>
                    <p className="text-gray-600 dark:text-gray-300">Devs</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
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
                Progress Reports
              </h1>
              <p className="text-gray-600 dark:text-gray-300">
                Comprehensive analytics and team performance insights
              </p>
            </div>

            {/* Tab Navigation */}
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-2 mb-8">
              <div className="flex space-x-1">
                {[
                  { id: 'weekly', label: 'Weekly Report', icon: Calendar },
                  { id: 'monthly', label: 'Monthly Report', icon: FileBarChart },
                  { id: 'team', label: 'Team Performance', icon: Users },
                  { id: 'trends', label: 'Productivity Trends', icon: TrendingUp }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
                      activeTab === tab.id
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                        : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    <tab.icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {loading && (
              <div className="flex items-center justify-center py-20">
                <div className="text-center">
                  <div className="animate-spin text-6xl mb-4">⚙️</div>
                  <p className="text-gray-600 dark:text-gray-300">Loading reports...</p>
                </div>
              </div>
            )}

            {!loading && (
              <>
                {activeTab === 'weekly' && renderWeeklyReport()}
                {activeTab === 'monthly' && renderMonthlyReport()}
                {activeTab === 'team' && renderTeamPerformance()}
                {activeTab === 'trends' && renderProductivityTrends()}
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
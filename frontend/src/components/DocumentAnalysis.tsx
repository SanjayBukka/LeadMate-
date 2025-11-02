import { useState, useEffect } from 'react';
import { FileText, Brain, Code, Clock, CheckCircle, AlertCircle } from 'lucide-react';

interface DocumentAnalysis {
  _id: string;
  filename: string;
  summary: string;
  stack_analysis: string;
  analyzed_at: string;
  status: 'completed' | 'error' | 'processing';
}

interface DocumentAnalysisProps {
  projectId: string;
}

export function DocumentAnalysis({ projectId }: DocumentAnalysisProps) {
  const [analyses, setAnalyses] = useState<DocumentAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadAnalyses();
  }, [projectId]);

  const loadAnalyses = async () => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`http://localhost:8000/api/documents/analysis/${projectId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAnalyses(data.analyses || []);
      } else {
        setError('Failed to load document analyses');
      }
    } catch (err) {
      console.error('Error loading analyses:', err);
      setError('Network error loading analyses');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-yellow-500 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Analysis Complete';
      case 'error':
        return 'Analysis Failed';
      case 'processing':
        return 'Analyzing...';
      default:
        return 'Unknown Status';
    }
  };

  if (loading) {
    return (
      <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600 dark:text-gray-300">Loading document analyses...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
        <div className="text-center py-8">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 dark:text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  if (analyses.length === 0) {
    return (
      <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
        <div className="text-center py-8">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            No Document Analysis Yet
          </h3>
          <p className="text-gray-600 dark:text-gray-300">
            Upload documents to see AI-powered analysis and insights
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Document Analysis
        </h2>
        <button
          onClick={loadAnalyses}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
        >
          Refresh
        </button>
      </div>

      <div className="space-y-4">
        {analyses.map((analysis) => (
          <div
            key={analysis._id}
            className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <FileText className="w-6 h-6 text-blue-500" />
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {analysis.filename}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Analyzed {new Date(analysis.analyzed_at).toLocaleString()}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {getStatusIcon(analysis.status)}
                <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
                  {getStatusText(analysis.status)}
                </span>
              </div>
            </div>

            {/* Summary Section */}
            <div className="mb-6">
              <div className="flex items-center space-x-2 mb-3">
                <Brain className="w-5 h-5 text-purple-500" />
                <h4 className="font-semibold text-gray-900 dark:text-white">Document Summary</h4>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                  {analysis.summary}
                </p>
              </div>
            </div>

            {/* Stack Analysis Section */}
            <div>
              <div className="flex items-center space-x-2 mb-3">
                <Code className="w-5 h-5 text-green-500" />
                <h4 className="font-semibold text-gray-900 dark:text-white">Technology Stack Analysis</h4>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                  {analysis.stack_analysis}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

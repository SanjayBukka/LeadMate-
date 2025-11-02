import { useState, useEffect } from 'react';
import { X, Calendar, User, FileText, Download, Loader2, AlertCircle, Sparkles, CheckCircle } from 'lucide-react';

interface Document {
  id: string;
  filename: string;
  size: number;
  contentType: string;
  uploadedAt: string;
  uploadedBy: string;
  extractedContent?: string | null;
}

interface Project {
  id: string;
  title: string;
  description: string;
  status: 'planning' | 'active' | 'completed' | 'on-hold' | 'cancelled';
  deadline: string;
  teamLead: string;
  progress: number;
  documents?: string[];
}

interface ProjectDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  project: Project | null;
}

export function ProjectDetailModal({ isOpen, onClose, project }: ProjectDetailModalProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzeStatus, setAnalyzeStatus] = useState<{success: boolean; message: string} | null>(null);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const token = localStorage.getItem('authToken');

  useEffect(() => {
    if (isOpen && project) {
      fetchDocuments();
    }
  }, [isOpen, project, token]);

  const fetchDocuments = async () => {
    if (!project) return;
    
    setIsLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/api/documents/project/${project.id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        
        // Backend returns { projectId, totalDocuments, documents }
        if (data && Array.isArray(data.documents)) {
          setDocuments(data.documents);
        } else if (Array.isArray(data)) {
          // Fallback if backend returns array directly
          setDocuments(data);
        } else {
          console.error('API returned unexpected data format:', data);
          setDocuments([]);
        }
      } else {
        const errorText = await response.text();
        console.error('Failed to load documents:', response.status, errorText);
        setError('Failed to load documents');
        setDocuments([]);
      }
    } catch (err) {
      console.error('Error fetching documents:', err);
      setError('Network error while loading documents');
      setDocuments([]);
    } finally {
      setIsLoading(false);
    }
  };

  const downloadDocument = async (documentId: string, filename: string) => {
    setDownloadingId(documentId);
    try {
      const response = await fetch(`${API_BASE_URL}/api/documents/download/${documentId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        setError('Failed to download document');
      }
    } catch (err) {
      console.error('Error downloading document:', err);
      setError('Network error while downloading');
    } finally {
      setDownloadingId(null);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const analyzeProjectDocuments = async () => {
    if (!project) return;
    
    setIsAnalyzing(true);
    setAnalyzeStatus(null);
    setError('');
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/doc/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          project_id: project.id,
          force_resync: true
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setAnalyzeStatus({
          success: data.success,
          message: data.message || 'Documents analyzed successfully!'
        });
        
        // Refresh documents after analysis
        setTimeout(() => {
          fetchDocuments();
        }, 1000);
      } else {
        const errorData = await response.json().catch(() => ({}));
        setAnalyzeStatus({
          success: false,
          message: errorData.detail || 'Failed to analyze documents'
        });
      }
    } catch (err) {
      console.error('Error analyzing documents:', err);
      setAnalyzeStatus({
        success: false,
        message: 'Network error while analyzing documents'
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'completed':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      case 'planning':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'on-hold':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400';
      case 'cancelled':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400';
    }
  };

  const getFileIcon = (contentType: string) => {
    if (contentType.includes('pdf')) return '📄';
    if (contentType.includes('image')) return '🖼️';
    if (contentType.includes('word') || contentType.includes('document')) return '📝';
    if (contentType.includes('excel') || contentType.includes('spreadsheet')) return '📊';
    if (contentType.includes('powerpoint') || contentType.includes('presentation')) return '📽️';
    if (contentType.includes('zip') || contentType.includes('compressed')) return '📦';
    if (contentType.includes('text')) return '📃';
    return '📎';
  };

  if (!isOpen || !project) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-2">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {project.title}
                </h2>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(project.status)}`}>
                  {project.status.charAt(0).toUpperCase() + project.status.slice(1)}
                </span>
              </div>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                {project.description}
              </p>
              
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                  <User className="w-4 h-4" />
                  <span>Team Lead: <span className="font-medium text-gray-900 dark:text-white">{project.teamLead}</span></span>
                </div>
                <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                  <Calendar className="w-4 h-4" />
                  <span>Deadline: <span className="font-medium text-gray-900 dark:text-white">{formatDate(project.deadline)}</span></span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mt-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Progress</span>
                  <span className="text-sm font-bold text-gray-900 dark:text-white">{project.progress}%</span>
                </div>
                <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
                    style={{ width: `${project.progress}%` }}
                  />
                </div>
              </div>
            </div>
            
            <button
              onClick={onClose}
              className="ml-4 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <X className="w-5 h-5 text-gray-600 dark:text-gray-300" />
            </button>
          </div>
        </div>

        {/* Documents Section */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-16rem)]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center space-x-2">
              <FileText className="w-5 h-5" />
              <span>Project Documents</span>
            </h3>
            <div className="flex items-center space-x-3">
              {documents.length > 0 && (
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {documents.length} {documents.length === 1 ? 'document' : 'documents'}
                </span>
              )}
              {documents.length > 0 && (
                <button
                  onClick={analyzeProjectDocuments}
                  disabled={isAnalyzing}
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 shadow-lg hover:shadow-xl"
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>Analyze Documents</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {analyzeStatus && (
            <div className={`mb-4 p-4 rounded-xl flex items-center space-x-3 ${
              analyzeStatus.success 
                ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-300' 
                : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-300'
            }`}>
              {analyzeStatus.success ? (
                <CheckCircle className="w-5 h-5 flex-shrink-0" />
              ) : (
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
              )}
              <p className="text-sm font-medium">{analyzeStatus.message}</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl mb-4 flex items-center space-x-3 bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm font-medium">{error}</p>
            </div>
          )}

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              <p className="ml-3 text-gray-600 dark:text-gray-300">Loading documents...</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">No documents uploaded yet</p>
              <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                The manager will upload project documents here
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                Check console (F12) for detailed logs
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {Array.isArray(documents) && documents.map((doc, index) => (
                <div
                  key={doc.id}
                  className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden"
                >
                  {/* Document Header */}
                  <div className="p-4 bg-gray-50 dark:bg-gray-700/50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3 flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <span className="text-2xl">{getFileIcon(doc.contentType)}</span>
                          <span className="font-bold text-blue-600 dark:text-blue-400 text-lg">
                            #{index + 1}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-gray-900 dark:text-white truncate">
                            {doc.filename}
                          </h4>
                          <div className="flex items-center space-x-2 mt-1 text-xs text-gray-500 dark:text-gray-400">
                            <span>{formatFileSize(doc.size)}</span>
                            <span>•</span>
                            <span>Uploaded {formatDate(doc.uploadedAt)}</span>
                            <span>•</span>
                            <span>By {doc.uploadedBy}</span>
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => downloadDocument(doc.id, doc.filename)}
                        disabled={downloadingId === doc.id}
                        className="ml-4 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                      >
                        {downloadingId === doc.id ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span className="text-sm font-medium">Downloading...</span>
                          </>
                        ) : (
                          <>
                            <Download className="w-4 h-4" />
                            <span className="text-sm font-medium">Download</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Extracted Content */}
                  {doc.extractedContent && (
                    <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                      <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center space-x-2">
                        <FileText className="w-4 h-4" />
                        <span>Document Content:</span>
                      </h5>
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        <div className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg border border-gray-200 dark:border-gray-700 max-h-96 overflow-y-auto">
                          {doc.extractedContent}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* No Content Message */}
                  {!doc.extractedContent && (
                    <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                      <p className="text-xs text-gray-500 dark:text-gray-400 italic text-center">
                        No text content could be extracted from this document
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <button
            onClick={onClose}
            className="w-full py-3 px-4 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-xl font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}


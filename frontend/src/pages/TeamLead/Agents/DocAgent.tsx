import { useState, useEffect, useRef } from 'react';
import { 
  FileText, 
  Send, 
  Loader2, 
  Sparkles, 
  AlertCircle,
  MessageCircle,
  FileBarChart,
  Brain
} from 'lucide-react';
import { Navbar } from '../../../components/Navbar';
import { Sidebar } from '../../../components/Sidebar';
import { ProtectedRoute } from '../../../components/ProtectedRoute';

interface Project {
  _id: string;
  title: string;
  description: string;
}

interface Document {
  id: string;
  filename: string;
  size: number;
  uploadedAt: string;
}

interface ChatMessage {
  user_message: string;
  agent_response: string;
}

export function DocAgent() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [summary, setSummary] = useState('');
  const [error, setError] = useState('');
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, []);

  // Load documents and chat history when project changes
  useEffect(() => {
    if (selectedProject) {
      loadDocuments();
      loadChatHistory();
    }
  }, [selectedProject]);

  // Auto scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const loadProjects = async () => {
    const token = localStorage.getItem('authToken');
    try {
      const response = await fetch(`${API_BASE_URL}/api/projects`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setProjects(data);
        if (data.length > 0 && !selectedProject) {
          setSelectedProject(data[0]._id);
        }
      }
    } catch (err) {
      console.error('Error loading projects:', err);
    }
  };

  const loadDocuments = async () => {
    if (!selectedProject) return;
    const token = localStorage.getItem('authToken');
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/documents/project/${selectedProject}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || []);
      }
    } catch (err) {
      console.error('Error loading documents:', err);
    }
  };

  const loadChatHistory = async () => {
    if (!selectedProject) return;
    const token = localStorage.getItem('authToken');
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/doc-agent/history/${selectedProject}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setChatHistory(data.history || []);
      }
    } catch (err) {
      console.error('Error loading chat history:', err);
    }
  };

  const handleSendQuestion = async () => {
    if (!question.trim() || !selectedProject || isLoading) return;

    const token = localStorage.getItem('authToken');
    const userQuestion = question.trim();
    setQuestion('');
    setError('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/doc-agent/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          project_id: selectedProject,
          question: userQuestion,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setChatHistory([...chatHistory, {
          user_message: userQuestion,
          agent_response: data.answer
        }]);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to get response from DocAgent');
      }
    } catch (err) {
      console.error('Error sending question:', err);
      setError('Network error. Please check your connection.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateSummary = async () => {
    if (!selectedProject || isSummarizing) return;

    const token = localStorage.getItem('authToken');
    setError('');
    setIsSummarizing(true);
    setSummary('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/doc-agent/summary`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          project_id: selectedProject,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSummary(data.summary);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to generate summary');
      }
    } catch (err) {
      console.error('Error generating summary:', err);
      setError('Network error. Please check your connection.');
    } finally {
      setIsSummarizing(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <ProtectedRoute requiredRole="teamlead">
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-cyan-50 dark:from-gray-900 dark:via-gray-800 dark:to-blue-900">
        <Navbar />
        
        <div className="flex">
          <Sidebar />
          
          <main className="flex-1 p-8">
            {/* Header */}
            <div className="mb-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-center">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                    DocAgent
                  </h1>
                  <p className="text-gray-600 dark:text-gray-300">
                    AI-powered document analysis & Q&A
                  </p>
                </div>
              </div>

              {/* Project Selector */}
              <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Select Project
                </label>
                <select
                  value={selectedProject}
                  onChange={(e) => setSelectedProject(e.target.value)}
                  className="w-full p-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
                >
                  {projects.length === 0 && <option value="">No projects available</option>}
                  {projects.map((project) => (
                    <option key={project._id} value={project._id}>
                      {project.title}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column - Documents & Summary */}
              <div className="space-y-6">
                {/* Project Documents */}
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
                    <FileText className="w-5 h-5" />
                    <span>Project Documents</span>
                    <span className="text-sm font-normal text-gray-500">({documents.length})</span>
                  </h3>
                  
                  {documents.length === 0 ? (
                    <div className="text-center py-8">
                      <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        No documents uploaded yet
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {documents.map((doc) => (
                        <div
                          key={doc.id}
                          className="p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600"
                        >
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {doc.filename}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {formatFileSize(doc.size)}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Generate Summary Button */}
                <button
                  onClick={handleGenerateSummary}
                  disabled={!selectedProject || documents.length === 0 || isSummarizing}
                  className="w-full py-3 px-4 rounded-xl font-semibold bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {isSummarizing ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Generating Summary...</span>
                    </>
                  ) : (
                    <>
                      <FileBarChart className="w-5 h-5" />
                      <span>Generate Project Summary</span>
                    </>
                  )}
                </button>

                {/* Summary Display */}
                {summary && (
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
                      <Sparkles className="w-5 h-5" />
                      <span>Project Summary</span>
                    </h3>
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      <div className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                        {summary}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Right Column - Chat Interface */}
              <div className="lg:col-span-2">
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl border border-gray-200 dark:border-gray-700 flex flex-col h-[calc(100vh-16rem)]">
                  {/* Chat Header */}
                  <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center space-x-2">
                      <MessageCircle className="w-5 h-5" />
                      <span>Chat with DocAgent</span>
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                      Ask questions about your project documents
                    </p>
                  </div>

                  {/* Error Display */}
                  {error && (
                    <div className="mx-6 mt-4 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 flex items-center space-x-3">
                      <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0" />
                      <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                    </div>
                  )}

                  {/* Chat Messages */}
                  <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {chatHistory.length === 0 ? (
                      <div className="text-center py-12">
                        <Brain className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                        <p className="text-gray-500 dark:text-gray-400 mb-2">
                          No conversation yet
                        </p>
                        <p className="text-sm text-gray-400 dark:text-gray-500">
                          Start by asking a question about your project documents
                        </p>
                      </div>
                    ) : (
                      chatHistory.map((msg, index) => (
                        <div key={index} className="space-y-4">
                          {/* User Message */}
                          <div className="flex justify-end">
                            <div className="bg-blue-500 text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-[80%]">
                              <p className="text-sm">{msg.user_message}</p>
                            </div>
                          </div>

                          {/* Agent Response */}
                          <div className="flex justify-start">
                            <div className="bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-2xl rounded-tl-sm px-4 py-3 max-w-[80%]">
                              <div className="flex items-center space-x-2 mb-2">
                                <Brain className="w-4 h-4 text-blue-500" />
                                <span className="text-xs font-semibold text-blue-500">DocAgent</span>
                              </div>
                              <div className="text-sm whitespace-pre-wrap">{msg.agent_response}</div>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                    
                    {/* Loading Indicator */}
                    {isLoading && (
                      <div className="flex justify-start">
                        <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl rounded-tl-sm px-4 py-3">
                          <div className="flex items-center space-x-2">
                            <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                            <span className="text-sm text-gray-600 dark:text-gray-300">DocAgent is thinking...</span>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    <div ref={chatEndRef} />
                  </div>

                  {/* Chat Input */}
                  <div className="p-6 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex space-x-3">
                      <input
                        type="text"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSendQuestion()}
                        placeholder={documents.length === 0 ? "Upload documents first..." : "Ask a question about your project..."}
                        disabled={!selectedProject || documents.length === 0 || isLoading}
                        className="flex-1 p-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      />
                      <button
                        onClick={handleSendQuestion}
                        disabled={!question.trim() || !selectedProject || documents.length === 0 || isLoading}
                        className="px-6 py-3 rounded-xl font-semibold bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                      >
                        <Send className="w-5 h-5" />
                        <span>Send</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </ProtectedRoute>
  );
}


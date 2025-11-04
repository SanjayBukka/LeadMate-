import React, { useState, useEffect, useRef } from 'react';
import { Navbar } from '../../components/Navbar';
import { Sidebar } from '../../components/Sidebar';
import { useAuth } from '../../contexts/AuthContext';
import { Send, Bot, User, Loader2, Sparkles, FileText, Users, CheckSquare, Settings, UserCheck, FolderOpen } from 'lucide-react';
import { LoadingIndicator } from '../../components/LoadingIndicator';

const API_BASE_URL = 'http://localhost:8000';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  agent: string;
  timestamp: Date;
}

interface Agent {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  endpoint: string;
}

const agents: Agent[] = [
  {
    id: 'document',
    name: 'Document Agent',
    description: 'Analyzes project documents and answers questions',
    icon: <FileText className="w-5 h-5" />,
    color: 'bg-blue-500',
    endpoint: '/api/agents/doc/chat'
  },
  {
    id: 'stack',
    name: 'Stack Agent',
    description: 'Helps with team formation and tech stack decisions',
    icon: <Users className="w-5 h-5" />,
    color: 'bg-green-500',
    endpoint: '/api/agents/stack/chat'
  },
  {
    id: 'team',
    name: 'Team Agent',
    description: 'Manages team members, roles, and team dynamics',
    icon: <UserCheck className="w-5 h-5" />,
    color: 'bg-orange-500',
    endpoint: '/api/agents/team/chat'
  }
];

interface Project {
  _id: string;
  title: string;
  description: string;
  status: string;
}

export function AIAgents() {
  const { user } = useAuth();
  const [agentMessages, setAgentMessages] = useState<{[key: string]: Message[]}>({});
  const [inputMessage, setInputMessage] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<Agent>(agents[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Get messages for current agent
  const messages = agentMessages[selectedAgent.id] || [];

  // FIX: Use startupId for company_id, user.id for lead_id
  const companyId = user?.startupId || 'demo_company';
  const leadId = user?.id || 'demo_lead';

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setIsLoadingProjects(true);
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}/api/projects`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setProjects(data);
        // Auto-select first project if available
        if (data.length > 0 && !selectedProject) {
          setSelectedProject(data[0]._id);
        }
      }
    } catch (err) {
      console.error('Error loading projects:', err);
    } finally {
      setIsLoadingProjects(false);
    }
  };

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat history on mount or when project changes
  useEffect(() => {
    loadChatHistory();
  }, [selectedAgent, selectedProject]);

  const loadChatHistory = async () => {
    try {
      // Use project_id if available, otherwise use lead_id (for backward compatibility)
      const contextId = selectedProject || leadId;
      
      let endpoint = '';
      if (selectedAgent.id === 'document') {
        endpoint = `/api/agents/doc/history/${companyId}/${contextId}`;
      } else if (selectedAgent.id === 'stack') {
        endpoint = `/api/agents/stack/history/${companyId}/${contextId}`;
      } else if (selectedAgent.id === 'task') {
        endpoint = `/api/agents/tasks/history/${companyId}/${contextId}`;
      }

      if (endpoint) {
        const token = localStorage.getItem('authToken');
        console.log('Loading chat history from:', `${API_BASE_URL}${endpoint}`);
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
          headers: {
            ...(token && { 'Authorization': `Bearer ${token}` }),
          },
        });
        
        console.log('Chat history response status:', response.status);
        
        if (response.ok) {
          const data = await response.json();
          console.log('Chat history data:', data);
          
          // Handle different response formats
          let messages = [];
          if (data.messages) {
            messages = data.messages;
          } else if (data.chat_history) {
            messages = data.chat_history;
          } else if (Array.isArray(data)) {
            messages = data;
          }
          
          if (messages && messages.length > 0) {
            const formattedMessages = messages.map((msg: any) => ({
              id: msg.id || Date.now().toString(),
              content: msg.content || msg.message || msg.response,
              role: msg.role || (msg.agent_response ? 'assistant' : 'user'),
              agent: selectedAgent.name,
              timestamp: new Date(msg.timestamp || Date.now())
            }));
            setAgentMessages(prev => ({
              ...prev,
              [selectedAgent.id]: formattedMessages
            }));
          }
        } else {
          console.error('Failed to load chat history:', response.status, response.statusText);
        }
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      role: 'user',
      agent: selectedAgent.name,
      timestamp: new Date()
    };

    setAgentMessages(prev => ({
      ...prev,
      [selectedAgent.id]: [...(prev[selectedAgent.id] || []), userMessage]
    }));
    const messageToSend = inputMessage;
    setInputMessage('');
    setIsLoading(true);
    setIsTyping(true);

    try {
      const token = localStorage.getItem('authToken');
      // Use project_id if available, otherwise use lead_id
      const contextId = selectedProject || leadId;
      
      const requestBody = {
        message: messageToSend,
        company_id: companyId,
        lead_id: contextId,
        project_id: selectedProject || undefined  // Include project_id if selected
      };

      console.log('Sending request to:', `${API_BASE_URL}${selectedAgent.endpoint}`);
      console.log('Request body:', requestBody);
      console.log('Selected agent:', selectedAgent);

      const response = await fetch(`${API_BASE_URL}${selectedAgent.endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
        body: JSON.stringify(requestBody)
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (response.ok) {
        const data = await response.json();
        console.log('Response data:', data);
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: data.response || data.message || 'I received your message but couldn\'t generate a response.',
          role: 'assistant',
          agent: selectedAgent.name,
          timestamp: new Date()
        };
        setAgentMessages(prev => ({
          ...prev,
          [selectedAgent.id]: [...(prev[selectedAgent.id] || []), assistantMessage]
        }));
      } else {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        
        let errorDetail = 'Sorry, I encountered an error. Please try again.';
        try {
          const errorData = JSON.parse(errorText);
          errorDetail = errorData.detail || errorData.message || errorDetail;
        } catch (e) {
          // If response is not JSON, use the text or status
          errorDetail = `Error ${response.status}: ${errorText || response.statusText}`;
        }

        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: errorDetail,
          role: 'assistant',
          agent: selectedAgent.name,
          timestamp: new Date()
        };
        setAgentMessages(prev => ({
          ...prev,
          [selectedAgent.id]: [...(prev[selectedAgent.id] || []), errorMessage]
        }));
      }
    } catch (error) {
      console.error('Error sending message:', error);
      console.error('Error details:', {
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined
      });
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Sorry, I couldn't connect to the server. Please check your connection. Error: ${error instanceof Error ? error.message : String(error)}`,
        role: 'assistant',
        agent: selectedAgent.name,
        timestamp: new Date()
      };
      setAgentMessages(prev => ({
        ...prev,
        [selectedAgent.id]: [...(prev[selectedAgent.id] || []), errorMessage]
      }));
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setAgentMessages(prev => ({
      ...prev,
      [selectedAgent.id]: []
    }));
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900">
      <Navbar />
      
      <div className="flex">
        <Sidebar />
        
        <main className="flex-1 flex flex-col h-screen">
          {/* Header */}
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl border-b border-gray-200 dark:border-gray-700 p-4">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl">
                    <Sparkles className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                      AI Agents Hub
                    </h1>
                    <p className="text-gray-600 dark:text-gray-300">
                      Chat with intelligent AI agents for your project
                    </p>
                  </div>
                </div>
                <button
                  onClick={clearChat}
                  className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  <Settings className="w-5 h-5" />
                </button>
              </div>
              
              {/* Project Selection */}
              <div className="flex items-center gap-3">
                <FolderOpen className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Select Project:
                </label>
                {isLoadingProjects ? (
                  <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
                ) : (
                  <select
                    value={selectedProject || ''}
                    onChange={(e) => setSelectedProject(e.target.value || null)}
                    className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-[200px]"
                  >
                    <option value="">All Projects</option>
                    {projects.map((project) => (
                      <option key={project._id} value={project._id}>
                        {project.title} ({project.status})
                      </option>
                    ))}
                  </select>
                )}
                {selectedProject && (
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Chat will focus on this project's documents
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Agent Selection */}
          <div className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl border-b border-gray-200 dark:border-gray-700 p-4">
            <div className="max-w-4xl mx-auto">
              <div className="flex gap-3 overflow-x-auto pb-2">
                {agents.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={() => setSelectedAgent(agent)}
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all whitespace-nowrap ${
                      selectedAgent.id === agent.id
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                        : 'bg-white/70 dark:bg-gray-700/70 text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-600'
                    }`}
                  >
                    <div className={`p-1 rounded-lg ${selectedAgent.id === agent.id ? 'bg-white/20' : agent.color}`}>
                      {agent.icon}
                    </div>
                    <div className="text-left">
                      <div className="font-semibold">{agent.name}</div>
                      <div className="text-xs opacity-80">{agent.description}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="max-w-4xl mx-auto">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="p-4 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl mb-4">
                    <Bot className="w-12 h-12 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    Welcome to {selectedAgent.name}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-300 mb-6 max-w-md">
                    {selectedAgent.description}. Start a conversation by typing a message below.
                  </p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {[
                      "What are the project requirements?",
                      "Help me form a team",
                      "Generate tasks for this project",
                      "Analyze the technical challenges"
                    ].map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => setInputMessage(suggestion)}
                        className="px-4 py-2 bg-white/70 dark:bg-gray-700/70 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-white dark:hover:bg-gray-600 transition-colors text-sm"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message, index) => (
                    <div
                      key={`${message.id}-${index}-${message.timestamp.getTime()}`}
                      className={`flex gap-3 ${
                        message.role === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      {message.role === 'assistant' && (
                        <div className={`p-2 rounded-xl ${selectedAgent.color} text-white`}>
                          {selectedAgent.icon}
                        </div>
                      )}
                      <div
                        className={`max-w-3xl px-4 py-3 rounded-2xl ${
                          message.role === 'user'
                            ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                            : 'bg-white/70 dark:bg-gray-700/70 text-gray-900 dark:text-white'
                        }`}
                      >
                        <div className="whitespace-pre-wrap">{message.content}</div>
                        <div className={`text-xs mt-2 opacity-70 ${
                          message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                        }`}>
                          {formatTime(message.timestamp)}
                        </div>
                      </div>
                      {message.role === 'user' && (
                        <div className="p-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl text-white">
                          <User className="w-5 h-5" />
                        </div>
                      )}
                    </div>
                  ))}
                  
                  {isTyping && (
                    <LoadingIndicator 
                      agent={selectedAgent.name} 
                      message="Analyzing your request and generating response..."
                    />
                  )}
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl border-t border-gray-200 dark:border-gray-700 p-4">
            <div className="max-w-4xl mx-auto">
              <div className="flex gap-3">
                <div className="flex-1 relative">
                  <textarea
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={`Ask ${selectedAgent.name} anything...`}
                    className="w-full px-4 py-3 pr-12 bg-white/70 dark:bg-gray-700/70 border border-gray-200 dark:border-gray-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                    rows={1}
                    style={{ minHeight: '52px', maxHeight: '120px' }}
                    disabled={isLoading}
                  />
                  <button
                    onClick={sendMessage}
                    disabled={!inputMessage.trim() || isLoading}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  >
                    {isLoading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
              <div className="flex items-center justify-between mt-2 text-xs text-gray-500 dark:text-gray-400">
                <span>Press Enter to send, Shift+Enter for new line</span>
                <span>Chatting with {selectedAgent.name}</span>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

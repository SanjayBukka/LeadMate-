import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FileText, 
  Layers, 
  Users, 
  Code, 
  Sparkles, 
  ArrowRight,
  Bot,
  Zap,
  Brain,
  TrendingUp
} from 'lucide-react';
import { Navbar } from '../../components/Navbar';
import { Sidebar } from '../../components/Sidebar';
import { ProtectedRoute } from '../../components/ProtectedRoute';

interface Agent {
  id: string;
  name: string;
  title: string;
  description: string;
  icon: any;
  color: string;
  gradient: string;
  features: string[];
  status: 'active' | 'coming-soon';
  path: string;
}

const agents: Agent[] = [
  {
    id: 'doc-agent',
    name: 'DocAgent',
    title: 'Document Analysis & Q&A',
    description: 'AI-powered document analyzer that reads your project documents, answers questions, identifies risks, and provides strategic recommendations.',
    icon: FileText,
    color: 'blue',
    gradient: 'from-blue-500 to-cyan-500',
    features: [
      'Analyze project documents',
      'Answer questions about requirements',
      'Risk assessment & analysis',
      'Strategic recommendations',
      'Chat with project docs'
    ],
    status: 'active',
    path: '/lead/agents/doc-agent'
  },
  {
    id: 'stack-agent',
    name: 'StackAgent',
    title: 'Tech Stack Recommendation',
    description: 'Intelligent tech stack advisor that analyzes your project requirements and recommends the best technology stack with reasoning.',
    icon: Layers,
    color: 'purple',
    gradient: 'from-purple-500 to-pink-500',
    features: [
      'Analyze project requirements',
      'Recommend technology stack',
      'Compare tech options',
      'Interactive discussion',
      'Export recommendations'
    ],
    status: 'active',
    path: '/lead/agents/stack-agent'
  },
  {
    id: 'team-agent',
    name: 'Team Formation',
    title: 'Team Building Assistant',
    description: 'Smart team formation agent that analyzes resumes, matches skills to requirements, and recommends optimal team structure.',
    icon: Users,
    color: 'green',
    gradient: 'from-green-500 to-emerald-500',
    features: [
      'Analyze resumes & CVs',
      'Match skills to requirements',
      'Recommend team structure',
      'Skill gap analysis',
      'Team composition insights'
    ],
    status: 'active',
    path: '/lead/agents/team-agent'
  },
  {
    id: 'code-clarity',
    name: 'CodeClarity AI',
    title: 'Repository Analysis',
    description: 'Advanced code analysis agent that examines GitHub repositories, provides developer insights, and answers questions about your codebase.',
    icon: Code,
    color: 'orange',
    gradient: 'from-orange-500 to-red-500',
    features: [
      'Analyze GitHub repositories',
      'Developer insights & metrics',
      'Code quality analysis',
      'Commit pattern analysis',
      'AI-powered code chat'
    ],
    status: 'active',
    path: '/lead/agents/code-clarity'
  }
];

const AgentCard = ({ agent }: { agent: Agent }) => {
  const navigate = useNavigate();
  const Icon = agent.icon;

  return (
    <div className="group relative bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 overflow-hidden">
      {/* Gradient Accent */}
      <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${agent.gradient}`} />
      
      {/* Status Badge */}
      {agent.status === 'coming-soon' && (
        <div className="absolute top-4 right-4 px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-xs font-semibold text-gray-600 dark:text-gray-300">
          Coming Soon
        </div>
      )}

      <div className="p-6">
        {/* Icon */}
        <div className={`w-16 h-16 rounded-2xl bg-gradient-to-r ${agent.gradient} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
          <Icon className="w-8 h-8 text-white" />
        </div>

        {/* Header */}
        <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          {agent.name}
        </h3>
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
          {agent.title}
        </p>
        
        {/* Description */}
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-4 line-clamp-3">
          {agent.description}
        </p>

        {/* Features */}
        <div className="space-y-2 mb-6">
          {agent.features.slice(0, 3).map((feature, index) => (
            <div key={index} className="flex items-center space-x-2 text-xs text-gray-600 dark:text-gray-400">
              <Sparkles className="w-3 h-3 text-gray-400" />
              <span>{feature}</span>
            </div>
          ))}
          {agent.features.length > 3 && (
            <p className="text-xs text-gray-500 dark:text-gray-500 italic">
              +{agent.features.length - 3} more features
            </p>
          )}
        </div>

        {/* Action Button */}
        <button
          onClick={() => agent.status === 'active' && navigate(agent.path)}
          disabled={agent.status !== 'active'}
          className={`w-full py-3 px-4 rounded-xl font-semibold transition-all duration-200 flex items-center justify-center space-x-2 ${
            agent.status === 'active'
              ? `bg-gradient-to-r ${agent.gradient} text-white hover:shadow-lg hover:scale-105`
              : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
          }`}
        >
          <span>{agent.status === 'active' ? 'Launch Agent' : 'Coming Soon'}</span>
          {agent.status === 'active' && <ArrowRight className="w-4 h-4" />}
        </button>
      </div>
    </div>
  );
};

export function AgentsHub() {
  return (
    <ProtectedRoute requiredRole="teamlead">
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900">
        <Navbar />
        
        <div className="flex">
          <Sidebar />
          
          <main className="flex-1 p-8">
            {/* Header Section */}
            <div className="mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                    AI Agents Hub
                  </h1>
                  <p className="text-gray-600 dark:text-gray-300">
                    Your AI-powered team for project success
                  </p>
                </div>
              </div>

              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center space-x-3">
                    <Bot className="w-8 h-8 text-blue-500" />
                    <div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">4</p>
                      <p className="text-xs text-gray-600 dark:text-gray-300">AI Agents</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center space-x-3">
                    <Zap className="w-8 h-8 text-purple-500" />
                    <div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">24/7</p>
                      <p className="text-xs text-gray-600 dark:text-gray-300">Available</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center space-x-3">
                    <Brain className="w-8 h-8 text-green-500" />
                    <div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">Smart</p>
                      <p className="text-xs text-gray-600 dark:text-gray-300">AI-Powered</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center space-x-3">
                    <TrendingUp className="w-8 h-8 text-orange-500" />
                    <div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">Fast</p>
                      <p className="text-xs text-gray-600 dark:text-gray-300">Instant Insights</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Agents Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {agents.map((agent) => (
                <AgentCard key={agent.id} agent={agent} />
              ))}
            </div>

            {/* Info Section */}
            <div className="mt-8 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-2xl p-6 border border-blue-200 dark:border-blue-800">
              <div className="flex items-start space-x-4">
                <div className="w-10 h-10 rounded-lg bg-blue-500 flex items-center justify-center flex-shrink-0">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    How It Works
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                    Each AI agent is powered by advanced language models and specialized for specific tasks. 
                    They work together to provide comprehensive project support:
                  </p>
                  <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
                    <li className="flex items-center space-x-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                      <span><strong>DocAgent</strong> reads and understands your project documents</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                      <span><strong>StackAgent</strong> recommends the best tech stack based on requirements</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                      <span><strong>Team Formation</strong> helps build the perfect team structure</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                      <span><strong>CodeClarity</strong> analyzes your codebase and provides insights</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </ProtectedRoute>
  );
}


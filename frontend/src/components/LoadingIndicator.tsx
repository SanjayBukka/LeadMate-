import { Loader2, Bot, Brain, Code, Users, CheckSquare } from 'lucide-react';

interface LoadingIndicatorProps {
  agent: string;
  message?: string;
}

export function LoadingIndicator({ agent, message = "Thinking..." }: LoadingIndicatorProps) {
  const getAgentIcon = (agentName: string) => {
    switch (agentName.toLowerCase()) {
      case 'document agent':
        return <Brain className="w-5 h-5 text-blue-500" />;
      case 'stack agent':
        return <Code className="w-5 h-5 text-green-500" />;
      case 'task agent':
        return <CheckSquare className="w-5 h-5 text-purple-500" />;
      case 'team agent':
        return <Users className="w-5 h-5 text-orange-500" />;
      default:
        return <Bot className="w-5 h-5 text-gray-500" />;
    }
  };

  const getAgentColor = (agentName: string) => {
    switch (agentName.toLowerCase()) {
      case 'document agent':
        return 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20';
      case 'stack agent':
        return 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20';
      case 'task agent':
        return 'border-purple-200 bg-purple-50 dark:border-purple-800 dark:bg-purple-900/20';
      case 'team agent':
        return 'border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-900/20';
      default:
        return 'border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900/20';
    }
  };

  return (
    <div className={`flex items-start space-x-3 p-4 rounded-lg border ${getAgentColor(agent)}`}>
      <div className="flex-shrink-0">
        {getAgentIcon(agent)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-sm font-medium text-gray-900 dark:text-white">
            {agent}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            is thinking...
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
          <span className="text-sm text-gray-600 dark:text-gray-300">
            {message}
          </span>
        </div>
        <div className="mt-2 flex space-x-1">
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
        </div>
      </div>
    </div>
  );
}

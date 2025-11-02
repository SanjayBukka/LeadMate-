import React from 'react';
import { Bot, User } from 'lucide-react';
import { ChatMessage } from '../data/mockData';

interface ChatBubbleProps {
  message: ChatMessage;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const isBot = message.isBot;

  return (
    <div className={`flex items-start space-x-3 mb-4 ${isBot ? '' : 'flex-row-reverse space-x-reverse'}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
        isBot 
          ? 'bg-gradient-to-br from-blue-500 to-purple-500' 
          : 'bg-gradient-to-br from-green-500 to-teal-500'
      }`}>
        {isBot ? (
          <Bot className="w-4 h-4 text-white" />
        ) : (
          <User className="w-4 h-4 text-white" />
        )}
      </div>
      <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${
        isBot
          ? 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200'
          : 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
      }`}>
        <p className="text-sm">{message.message}</p>
        <p className={`text-xs mt-1 ${
          isBot ? 'text-gray-500 dark:text-gray-400' : 'text-blue-100'
        }`}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}
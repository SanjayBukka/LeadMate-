import React, { useState } from 'react';
import { Send, Bot } from 'lucide-react';
import { Navbar } from '../../components/Navbar';
import { Sidebar } from '../../components/Sidebar';
import { ChatBubble } from '../../components/ChatBubble';

// Define the message interface
interface ChatMessage {
  id: string;
  message: string;
  isBot: boolean;
  timestamp: string;
}

export function AIAssistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      message: 'Hello! How can I assist you today?',
      isBot: true,
      timestamp: new Date().toISOString()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    // Add user message to chat
    const newUserMessage: ChatMessage = {
      id: Date.now().toString(),
      message: inputMessage,
      isBot: false,
      timestamp: new Date().toISOString()
    };

    setMessages((prev: ChatMessage[]) => [...prev, newUserMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Send message to backend API
      const response = await fetch('http://localhost:8000/api/assistant/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: inputMessage }),
      });

      if (response.ok) {
        const data = await response.json();
        // Add bot response to chat
        setMessages((prev: ChatMessage[]) => [...prev, ...data.messages]);
      } else {
        // Add error message if API call fails
        const errorMessage: ChatMessage = {
          id: Date.now().toString(),
          message: 'Sorry, I encountered an error. Please try again.',
          isBot: true,
          timestamp: new Date().toISOString()
        };
        setMessages((prev: ChatMessage[]) => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message if network error
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        message: 'Network error. Please check your connection and try again.',
        isBot: true,
        timestamp: new Date().toISOString()
      };
      setMessages((prev: ChatMessage[]) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900">
      <Navbar />
      
      <div className="flex">
        <Sidebar />
        
        <main className="flex-1 p-8">
          <div className="max-w-4xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                AI Assistant
              </h1>
              <p className="text-gray-600 dark:text-gray-300">
                Get help with project management and team coordination
              </p>
            </div>

            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg h-[600px] flex flex-col">
              {/* Chat Header */}
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-gray-900 dark:text-white">
                      TeamFlow Assistant
                    </h2>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      Always here to help
                    </p>
                  </div>
                </div>
              </div>

              {/* Chat Messages */}
              <div className="flex-1 p-6 overflow-y-auto">
                <div className="space-y-4">
                  {messages.map((message) => (
                    <ChatBubble key={message.id} message={message} />
                  ))}
                </div>
              </div>

              {/* Chat Input */}
              <form onSubmit={handleSendMessage} className="p-6 border-t border-gray-200 dark:border-gray-700">
                <div className="flex space-x-4">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Type your message..."
                    className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/50 dark:bg-gray-700/50"
                  />
                  <button
                    type="submit"
                    className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-3 rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all duration-200"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </form>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
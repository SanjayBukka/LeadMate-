import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Kanban,
  Users,
  Bot,
  FileBarChart,
  Sparkles
} from 'lucide-react';

const sidebarItems = [
  {
    to: '/lead/dashboard',
    icon: LayoutDashboard,
    label: 'Dashboard'
  },
  {
    to: '/lead/taskboard',
    icon: Kanban,
    label: 'Task Board'
  },
  {
    to: '/lead/members',
    icon: Users,
    label: 'Team Members'
  },
  {
    to: '/lead/agents',
    icon: Sparkles,
    label: 'AI Agents',
    highlight: true
  },
  {
    to: '/lead/management',
    icon: FileBarChart,
    label: 'Management'
  }
];

export function Sidebar() {
  return (
    <aside className="w-64 bg-white/50 dark:bg-gray-900/50 backdrop-blur-xl border-r border-gray-200 dark:border-gray-700 min-h-screen p-4 shadow-sm">
      <nav className="space-y-1.5">
        {sidebarItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-4 py-3.5 rounded-xl transition-all duration-200 relative group ${
                isActive
                  ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg shadow-blue-500/50 dark:shadow-blue-500/30'
                  : item.highlight
                  ? 'hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 dark:hover:from-blue-900/20 dark:hover:to-purple-900/20 text-gray-700 dark:text-gray-300 border-2 border-blue-200 dark:border-blue-800/50 hover:border-blue-300 dark:hover:border-blue-700'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 hover:shadow-md'
              }`
            }
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            <span className="font-semibold">{item.label}</span>
            {item.highlight && !window.location.pathname.includes(item.to) && (
              <>
                <span className="absolute top-2 right-2 w-2 h-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full animate-pulse" />
                <span className="absolute top-1 right-1 w-4 h-4 bg-blue-500/20 rounded-full animate-ping" />
              </>
            )}
          </NavLink>
        ))}
      </nav>
      
      {/* Footer Info */}
      <div className="mt-8 p-4 rounded-xl bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border border-blue-100 dark:border-blue-800/50">
        <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
          💡 Pro Tip
        </p>
        <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
          Use AI Agents to automate your workflow and boost productivity!
        </p>
      </div>
    </aside>
  );
}
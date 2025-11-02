import React from 'react';
import { Calendar, User, AlertCircle } from 'lucide-react';
import { Task } from '../data/mockData';

interface TaskCardProps {
  task: Task;
  onDragStart?: (e: React.DragEvent, taskId: string) => void;
}

export function TaskCard({ task, onDragStart }: TaskCardProps) {
  const priorityColors = {
    high: 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20',
    medium: 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20',
    low: 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
  };

  const priorityTextColors = {
    high: 'text-red-700 dark:text-red-300',
    medium: 'text-yellow-700 dark:text-yellow-300',
    low: 'text-green-700 dark:text-green-300'
  };

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart?.(e, task.id)}
      className={`p-4 rounded-xl border-2 cursor-move hover:shadow-md transition-all duration-200 ${priorityColors[task.priority]}`}
    >
      <div className="flex items-start justify-between mb-3">
        <h4 className="font-semibold text-gray-900 dark:text-white text-sm">
          {task.title}
        </h4>
        <div className="flex items-center space-x-1">
          <AlertCircle className={`w-3 h-3 ${priorityTextColors[task.priority]}`} />
          <span className={`text-xs font-medium capitalize ${priorityTextColors[task.priority]}`}>
            {task.priority}
          </span>
        </div>
      </div>

      <p className="text-xs text-gray-600 dark:text-gray-300 mb-3">
        {task.description}
      </p>

      <div className="space-y-2">
        <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
          <User className="w-3 h-3 mr-2" />
          {task.assignee}
        </div>
        <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
          <Calendar className="w-3 h-3 mr-2" />
          {new Date(task.dueDate).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
}
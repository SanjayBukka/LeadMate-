import { Calendar, User, TrendingUp, Clock, Trash2 } from 'lucide-react';
import { Project } from '../data/mockData';

interface ProjectCardProps {
  project: Project;
  onClick?: () => void;
  onDelete?: (projectId: string) => void;
  showDeleteButton?: boolean;
}

export function ProjectCard({ project, onClick, onDelete, showDeleteButton = false }: ProjectCardProps) {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'completed':
        return {
          bg: 'bg-green-100 dark:bg-green-900/30',
          text: 'text-green-700 dark:text-green-400',
          label: 'Completed',
          icon: '✓'
        };
      case 'active':
        return {
          bg: 'bg-blue-100 dark:bg-blue-900/30',
          text: 'text-blue-700 dark:text-blue-400',
          label: 'Active',
          icon: '▶'
        };
      case 'planning':
        return {
          bg: 'bg-purple-100 dark:bg-purple-900/30',
          text: 'text-purple-700 dark:text-purple-400',
          label: 'Planning',
          icon: '◉'
        };
      case 'on-hold':
        return {
          bg: 'bg-yellow-100 dark:bg-yellow-900/30',
          text: 'text-yellow-700 dark:text-yellow-400',
          label: 'On Hold',
          icon: '⏸'
        };
      default:
        return {
          bg: 'bg-gray-100 dark:bg-gray-700',
          text: 'text-gray-700 dark:text-gray-300',
          label: status,
          icon: '●'
        };
    }
  };

  const statusConfig = getStatusConfig(project.status);
  const progressColor = project.progress >= 75 ? 'green' : project.progress >= 50 ? 'blue' : 'yellow';

  const dueDateIn3Months = new Date();
  dueDateIn3Months.setMonth(dueDateIn3Months.getMonth() + 3);

  return (
    <div 
      onClick={onClick}
      className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 cursor-pointer group">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors line-clamp-1">
          {project.title}
        </h3>
        <div className="flex items-center space-x-2">
          {showDeleteButton && onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (window.confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
                  onDelete(project.id);
                }
              }}
              className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
              title="Delete Project"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
          <span
            className={`px-3 py-1 rounded-lg text-xs font-semibold ${statusConfig.bg} ${statusConfig.text} flex items-center space-x-1`}
          >
            <span>{statusConfig.icon}</span>
            <span>{statusConfig.label}</span>
          </span>
        </div>
      </div>

      {/* Description */}
      <p className="text-gray-600 dark:text-gray-300 text-sm mb-4 line-clamp-2 leading-relaxed">
        {project.description}
      </p>

      {/* Info Grid */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 p-2 rounded-lg">
          <Calendar className="w-4 h-4 mr-2 flex-shrink-0 text-blue-500" />
          <span className="font-medium">Due:</span>
          <span className="ml-1">{dueDateIn3Months.toLocaleDateString()}</span>
        </div>
        <div className="flex items-center text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 p-2 rounded-lg">
          <User className="w-4 h-4 mr-2 flex-shrink-0 text-purple-500" />
          <span className="font-medium">Lead:</span>
          <span className="ml-1 truncate">{project.teamLead}</span>
        </div>
      </div>

      {/* Progress Section */}
      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <TrendingUp className={`w-4 h-4 ${
              project.progress >= 75 ? 'text-green-500' :
              project.progress >= 50 ? 'text-blue-500' :
              'text-yellow-500'
            }`} />
            <span className="text-sm font-bold text-gray-700 dark:text-gray-300">
              {project.progress}%
            </span>
          </div>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Progress
          </span>
        </div>
        <div className="w-full h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full bg-gradient-to-r transition-all duration-500 ${
              progressColor === 'green'
                ? 'from-green-400 to-green-600'
                : progressColor === 'blue'
                ? 'from-blue-400 to-blue-600'
                : 'from-yellow-400 to-yellow-600'
            }`}
            style={{ width: `${project.progress}%` }}
          />
        </div>
      </div>
    </div>
  );
}
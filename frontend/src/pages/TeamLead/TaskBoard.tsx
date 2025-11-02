import React, { useState, useEffect } from 'react';
import { Navbar } from '../../components/Navbar';
import { Sidebar } from '../../components/Sidebar';
import { TaskCard } from '../../components/TaskCard';
import { useAuth } from '../../contexts/AuthContext';

const API_BASE_URL = 'http://localhost:8000';

const columns = [
  { id: 'todo', title: 'To Do', color: 'border-gray-300' },
  { id: 'inprogress', title: 'In Progress', color: 'border-blue-300' },
  { id: 'completed', title: 'Completed', color: 'border-green-300' }
];

export function TaskBoard() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<any[]>([]);
  const [draggedTask, setDraggedTask] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [projectComplete, setProjectComplete] = useState(false);
  const [showCompletionModal, setShowCompletionModal] = useState(false);

  // Use user ID for both company and lead (can be enhanced later)
  const companyId = user?.id || 'demo_company';
  const leadId = user?.id || 'demo_lead';

  // Fetch tasks from backend
  const fetchTasks = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/tasks/${companyId}/${leadId}`);
      if (response.ok) {
        const data = await response.json();
        setTasks(data.tasks || []);
      } else {
        console.error('Failed to fetch tasks');
      }
    } catch (error) {
      console.error('Error fetching tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch task statistics
  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/tasks/stats/${companyId}/${leadId}`);
      if (response.ok) {
        const data = await response.json();
        setStats(data.statistics);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  // Generate tasks using AI
  const generateTasks = async () => {
    setGenerating(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/tasks/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: companyId,
          lead_id: leadId,
          project_name: 'My Project'
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          alert(`✅ Generated ${data.tasks_generated} tasks successfully!`);
          setTasks(data.tasks || []);
          fetchStats();
        } else {
          alert(`⚠️ ${data.error || 'Failed to generate tasks'}`);
        }
      } else {
        alert('❌ Failed to generate tasks');
      }
    } catch (error) {
      console.error('Error generating tasks:', error);
      alert('❌ Error generating tasks');
    } finally {
      setGenerating(false);
    }
  };

  // Check project completion
  const checkProjectCompletion = (tasks: any[]) => {
    const totalTasks = tasks.length;
    const completedTasks = tasks.filter(task => task.status === 'completed').length;
    
    if (totalTasks > 0 && completedTasks === totalTasks) {
      setProjectComplete(true);
      setShowCompletionModal(true);
    } else {
      setProjectComplete(false);
    }
  };

  // Load tasks on mount
  useEffect(() => {
    fetchTasks();
    fetchStats();
  }, [companyId, leadId]);

  // Check completion when tasks change
  useEffect(() => {
    checkProjectCompletion(tasks);
  }, [tasks]);

  const handleDragStart = (e: React.DragEvent, taskId: string) => {
    setDraggedTask(taskId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = async (e: React.DragEvent, columnId: string) => {
    e.preventDefault();
    if (draggedTask) {
      try {
        // Update backend
        const response = await fetch(`${API_BASE_URL}/api/agents/tasks/status`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            task_id: draggedTask,
            new_status: columnId,
            company_id: companyId,
            lead_id: leadId
          })
        });

        if (response.ok) {
          // Update local state
          const updatedTasks = tasks.map(task =>
            task.id === draggedTask
              ? { ...task, status: columnId as 'todo' | 'inprogress' | 'completed' }
              : task
          );
          setTasks(updatedTasks);
          fetchStats(); // Refresh statistics
          
          // Check if project is complete after this move
          checkProjectCompletion(updatedTasks);
        } else {
          alert('Failed to update task status');
        }
      } catch (error) {
        console.error('Error updating task:', error);
        alert('Error updating task');
      }
      setDraggedTask(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900">
      <Navbar />
      
      <div className="flex">
        <Sidebar />
        
        <main className="flex-1 p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                    Task Board
                  </h1>
                  <p className="text-gray-600 dark:text-gray-300">
                    Manage tasks with drag-and-drop functionality
                  </p>
                </div>
                <button
                  onClick={generateTasks}
                  disabled={generating}
                  className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {generating ? (
                    <>
                      <span className="animate-spin">⚙️</span>
                      Generating...
                    </>
                  ) : (
                    <>
                      <span>🤖</span>
                      Generate Tasks with AI
                    </>
                  )}
                </button>
              </div>

              {/* Statistics */}
              {stats && (
                <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                    <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {stats.total_tasks}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Total Tasks</div>
                  </div>
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {stats.completion_rate}%
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Completion</div>
                  </div>
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                    <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                      {stats.in_progress}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">In Progress</div>
                  </div>
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                    <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                      {stats.high_priority}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">High Priority</div>
                  </div>
                  <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                    <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                      {stats.overdue || 0}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Overdue</div>
                  </div>
                </div>
              )}
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-20">
                <div className="text-center">
                  <div className="animate-spin text-6xl mb-4">⚙️</div>
                  <p className="text-gray-600 dark:text-gray-400">Loading tasks...</p>
                </div>
              </div>
            ) : tasks.length === 0 ? (
              <div className="flex items-center justify-center py-20">
                <div className="text-center">
                  <div className="text-6xl mb-4">📋</div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    No tasks yet
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-4">
                    Click "Generate Tasks with AI" to create tasks automatically
                  </p>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {columns.map((column) => (
                  <div
                    key={column.id}
                    className={`bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl rounded-2xl border-2 ${column.color} dark:border-gray-600 p-4 min-h-[600px]`}
                    onDragOver={handleDragOver}
                    onDrop={(e) => handleDrop(e, column.id)}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="font-semibold text-gray-900 dark:text-white">
                        {column.title}
                      </h2>
                      <span className="bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs px-2 py-1 rounded-full">
                        {tasks.filter(task => task.status === column.id).length}
                      </span>
                    </div>
                    
                    <div className="space-y-3">
                      {tasks
                        .filter(task => task.status === column.id)
                        .map((task) => (
                          <TaskCard
                            key={task.id}
                            task={task}
                            onDragStart={handleDragStart}
                          />
                        ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Project Completion Modal */}
      {showCompletionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 max-w-md mx-4 text-center shadow-2xl">
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              Project Completed!
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Congratulations! All tasks have been completed successfully. 
              Your project is now ready for delivery.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowCompletionModal(false)}
                className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                Close
              </button>
              <button
                onClick={() => {
                  setShowCompletionModal(false);
                  // Add logic to start new project or export results
                }}
                className="flex-1 px-4 py-2 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-lg hover:from-green-700 hover:to-blue-700 transition-all"
              >
                Start New Project
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
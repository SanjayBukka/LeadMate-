import { useState, useEffect } from 'react';
import { TrendingUp, Clock, CheckCircle, Users } from 'lucide-react';
import { Navbar } from '../../components/Navbar';
import { Sidebar } from '../../components/Sidebar';
import { ProjectCard } from '../../components/ProjectCard';
import { ProjectDetailModal } from '../../components/ProjectDetailModal';
import { DocumentAnalysis } from '../../components/DocumentAnalysis';
import { ProtectedRoute } from '../../components/ProtectedRoute';

interface Project {
  _id: string;
  title: string;
  description: string;
  deadline: string;
  status: 'active' | 'completed';
  progress: number;
  teamLead: string;
  createdAt: string;
}

export function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const token = localStorage.getItem('authToken');

  const handleProjectClick = (project: Project) => {
    setSelectedProject(project);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedProject(null);
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/projects', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setProjects(data);
      } else {
        setError('Failed to load projects');
      }
    } catch (err) {
      console.error('Error loading projects:', err);
      setError('Network error loading projects');
    } finally {
      setIsLoading(false);
    }
  };

  const activeProjects = projects.filter(p => p.status === 'active');
  const completedProjects = projects.filter(p => p.status === 'completed');
  
  // Calculate due this week
  const today = new Date();
  const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
  const dueThisWeek = activeProjects.filter(p => {
    const deadline = new Date(p.deadline);
    return deadline >= today && deadline <= nextWeek;
  });

  return (
    <ProtectedRoute requiredRole="teamlead">
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900">
        <Navbar />
        
        <div className="flex">
          <Sidebar />
          
          <main className="flex-1 p-4 sm:p-8">
            <div className="max-w-7xl mx-auto">
              <div className="mb-8">
                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2">
                  Team Lead Dashboard
                </h1>
                <p className="text-sm sm:text-base text-gray-600 dark:text-gray-300">
                  Monitor your assigned projects and track progress
                </p>
              </div>

              {/* Error Message */}
              {error && (
                <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-600 dark:text-red-400">
                  {error}
                </div>
              )}

              {/* Statistics Cards */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-8">
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-4 sm:p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
                  <div className="flex items-center space-x-2 sm:space-x-3">
                    <div className="w-10 h-10 sm:w-12 sm:h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
                      <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                        {isLoading ? '...' : activeProjects.length}
                      </p>
                      <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 truncate">Active Projects</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-4 sm:p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
                  <div className="flex items-center space-x-2 sm:space-x-3">
                    <div className="w-10 h-10 sm:w-12 sm:h-12 bg-green-100 dark:bg-green-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
                      <CheckCircle className="w-5 h-5 sm:w-6 sm:h-6 text-green-600 dark:text-green-400" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                        {isLoading ? '...' : completedProjects.length}
                      </p>
                      <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 truncate">Completed</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-4 sm:p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
                  <div className="flex items-center space-x-2 sm:space-x-3">
                    <div className="w-10 h-10 sm:w-12 sm:h-12 bg-purple-100 dark:bg-purple-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
                      <Users className="w-5 h-5 sm:w-6 sm:h-6 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                        {isLoading ? '...' : projects.length}
                      </p>
                      <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 truncate">Total Projects</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-4 sm:p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
                  <div className="flex items-center space-x-2 sm:space-x-3">
                    <div className="w-10 h-10 sm:w-12 sm:h-12 bg-yellow-100 dark:bg-yellow-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
                      <Clock className="w-5 h-5 sm:w-6 sm:h-6 text-yellow-600 dark:text-yellow-400" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                        {isLoading ? '...' : dueThisWeek.length}
                      </p>
                      <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 truncate">Due This Week</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Loading State */}
              {isLoading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-4 text-gray-600 dark:text-gray-300">Loading your projects...</p>
                </div>
              ) : projects.length === 0 ? (
                /* Empty State */
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-12 text-center">
                  <TrendingUp className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    No Projects Assigned Yet
                  </h3>
                  <p className="text-gray-600 dark:text-gray-300">
                    Your manager will assign projects to you soon
                  </p>
                </div>
              ) : (
                /* Projects Sections */
                <div className="space-y-8">
                  {activeProjects.length > 0 && (
                    <div>
                      <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white mb-4">
                        Active Projects
                      </h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                        {activeProjects.map((project) => (
                          <ProjectCard 
                            key={project._id} 
                            project={{
                              id: project._id,
                              title: project.title,
                              description: project.description,
                              deadline: project.deadline,
                              status: project.status,
                              progress: project.progress,
                              teamLead: project.teamLead,
                              createdAt: project.createdAt
                            }}
                            onClick={() => handleProjectClick(project)}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {completedProjects.length > 0 && (
                    <div>
                      <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white mb-4">
                        Completed Projects
                      </h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                        {completedProjects.map((project) => (
                          <ProjectCard 
                            key={project._id} 
                            project={{
                              id: project._id,
                              title: project.title,
                              description: project.description,
                              deadline: project.deadline,
                              status: project.status,
                              progress: project.progress,
                              teamLead: project.teamLead,
                              createdAt: project.createdAt
                            }}
                            onClick={() => handleProjectClick(project)}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Document Analysis Section */}
              {projects.length > 0 && (
                <div className="mt-8">
                  <DocumentAnalysis projectId={projects[0]._id} />
                </div>
              )}
            </div>
          </main>
        </div>

        {/* Project Detail Modal */}
        <ProjectDetailModal
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          project={selectedProject ? {
            id: selectedProject._id,
            title: selectedProject.title,
            description: selectedProject.description,
            status: selectedProject.status,
            deadline: selectedProject.deadline,
            teamLead: selectedProject.teamLead,
            progress: selectedProject.progress,
          } : null}
        />
      </div>
    </ProtectedRoute>
  );
}

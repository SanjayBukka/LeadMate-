import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Users, TrendingUp, Calendar, UsersRound } from 'lucide-react';
import { Navbar } from '../../components/Navbar';
import { ProjectCard } from '../../components/ProjectCard';
import { CreateProjectModal } from './CreateProjectModal';
import { EditProjectModal } from './EditProjectModal';

interface Project {
  _id: string;
  title: string;
  description: string;
  deadline: string;
  status: 'planning' | 'active' | 'completed' | 'on-hold' | 'cancelled';
  progress: number;
  teamLead: string;
  teamLeadId: string;
  createdAt: string;
}

interface DashboardStats {
  activeProjects: number;
  completedProjects: number;
  totalTeamLeads: number;
}

export function ManagerDashboard() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    activeProjects: 0,
    completedProjects: 0,
    totalTeamLeads: 0
  });
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const token = localStorage.getItem('authToken');

  const handleProjectClick = (project: Project) => {
    setSelectedProject(project);
    setIsEditModalOpen(true);
  };

  const handleCloseEditModal = () => {
    setIsEditModalOpen(false);
    setSelectedProject(null);
  };

  const handleDeleteProject = async (projectId: string) => {
    if (deleteConfirm !== projectId) {
      setDeleteConfirm(projectId);
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/projects/${projectId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        // Remove project from state
        setProjects(projects.filter(p => p._id !== projectId));
        
        // Update stats
        const deletedProject = projects.find(p => p._id === projectId);
        if (deletedProject) {
          setStats(prevStats => ({
            ...prevStats,
            activeProjects: deletedProject.status === 'active' ? prevStats.activeProjects - 1 : prevStats.activeProjects,
            completedProjects: deletedProject.status === 'completed' ? prevStats.completedProjects - 1 : prevStats.completedProjects
          }));
        }
        
        setDeleteConfirm(null);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to delete project');
      }
    } catch (err) {
      console.error('Error deleting project:', err);
      setError('Network error. Please try again.');
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      // Load projects and team leads in parallel
      const [projectsResponse, teamLeadsResponse] = await Promise.all([
        fetch('http://localhost:8000/api/projects', {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch('http://localhost:8000/api/auth/users/team-leads', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      let loadedProjects: Project[] = [];
      let teamLeadsCount = 0;

      // Handle projects
      if (projectsResponse.ok) {
        loadedProjects = await projectsResponse.json();
        setProjects(loadedProjects);
      }

      // Handle team leads
      if (teamLeadsResponse.ok) {
        const teamLeads = await teamLeadsResponse.json();
        teamLeadsCount = teamLeads.filter((lead: any) => lead.isActive).length;
      }

      // Calculate stats
      const activeCount = loadedProjects.filter(p => p.status === 'active').length;
      const completedCount = loadedProjects.filter(p => p.status === 'completed').length;

      setStats({
        activeProjects: activeCount,
        completedProjects: completedCount,
        totalTeamLeads: teamLeadsCount
      });

    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateProject = async (projectData: any) => {
    try {
      const response = await fetch('http://localhost:8000/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          title: projectData.title,
          description: projectData.description,
          deadline: projectData.deadline,
          teamLeadId: projectData.teamLeadId
        }),
      });

      if (response.ok) {
        const newProject = await response.json();
        
        // Upload documents if any with progress tracking
        if (projectData.files && projectData.files.length > 0) {
          const formData = new FormData();
          projectData.files.forEach((file: File) => {
            formData.append('files', file);
          });

          try {
            // Create XMLHttpRequest for progress tracking
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (event) => {
              if (event.lengthComputable) {
                const percentComplete = (event.loaded / event.total) * 100;
                // You can emit this progress to the modal if needed
                console.log(`Upload progress: ${percentComplete}%`);
              }
            });

            xhr.addEventListener('load', () => {
              if (xhr.status === 200) {
                console.log('Documents uploaded successfully');
              } else {
                console.error('Document upload failed:', xhr.statusText);
              }
            });

            xhr.open('POST', `http://localhost:8000/api/documents/upload/${newProject._id}`);
            xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            xhr.send(formData);
          } catch (uploadError) {
            console.error('Error uploading documents:', uploadError);
            // Don't fail project creation if document upload fails
          }
        }

        setProjects([newProject, ...projects]);
        setStats({
          ...stats,
          activeProjects: stats.activeProjects + 1
        });
        setIsCreateModalOpen(false);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create project');
      }
    } catch (err) {
      console.error('Error creating project:', err);
      setError('Network error. Please try again.');
    }
  };

  const activeProjects = projects.filter(p => p.status === 'active');
  const completedProjects = projects.filter(p => p.status === 'completed');

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900">
      <Navbar />
      
      <div className="p-4 sm:p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header Section */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2">
                Manager Dashboard
              </h1>
              <p className="text-sm sm:text-base text-gray-600 dark:text-gray-300">
                Oversee all projects and team performance
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => navigate('/manager/team')}
                className="w-full sm:w-auto bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 px-4 sm:px-6 py-3 rounded-xl font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-200 flex items-center justify-center space-x-2 shadow-lg border border-gray-200 dark:border-gray-700"
              >
                <UsersRound className="w-5 h-5" />
                <span>Manage Team</span>
              </button>
            <button
                onClick={() => setIsCreateModalOpen(true)}
                className="w-full sm:w-auto bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 sm:px-6 py-3 rounded-xl font-medium hover:from-blue-700 hover:to-purple-700 transition-all duration-200 flex items-center justify-center space-x-2 shadow-lg"
            >
              <Plus className="w-5 h-5" />
              <span>New Project</span>
            </button>
          </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-600 dark:text-red-400">
              {error}
            </div>
          )}

          {/* Statistics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-8">
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
                  <TrendingUp className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="min-w-0">
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {isLoading ? '...' : stats.activeProjects}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-300 truncate">Active Projects</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
                  <Calendar className="w-6 h-6 text-green-600 dark:text-green-400" />
                </div>
                <div className="min-w-0">
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {isLoading ? '...' : stats.completedProjects}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-300 truncate">Completed</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
                  <Users className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                </div>
                <div className="min-w-0">
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {isLoading ? '...' : stats.totalTeamLeads}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-300 truncate">Team Leads</p>
                </div>
              </div>
            </div>
          </div>

          {/* Loading State */}
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-300">Loading projects...</p>
            </div>
          ) : projects.length === 0 ? (
            /* Empty State */
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-12 text-center">
              <TrendingUp className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                No Projects Yet
              </h3>
              <p className="text-gray-600 dark:text-gray-300 mb-6">
                Get started by creating your first project
              </p>
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl font-medium hover:from-blue-700 hover:to-purple-700 transition-all duration-200"
              >
                Create First Project
              </button>
            </div>
          ) : (
            /* Projects Grid */
          <div className="space-y-8">
              {activeProjects.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
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
                        onDelete={handleDeleteProject}
                        showDeleteButton={true}
                      />
                ))}
              </div>
            </div>
              )}

            {completedProjects.length > 0 && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
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
                        onDelete={handleDeleteProject}
                        showDeleteButton={true}
                      />
                  ))}
                </div>
              </div>
            )}
          </div>
          )}
        </div>
      </div>

      <CreateProjectModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreateProject}
      />

      <EditProjectModal
        isOpen={isEditModalOpen}
        onClose={handleCloseEditModal}
        project={selectedProject ? {
          id: selectedProject._id,
          title: selectedProject.title,
          description: selectedProject.description,
          status: selectedProject.status,
          deadline: selectedProject.deadline,
          teamLeadId: selectedProject.teamLeadId,
          teamLead: selectedProject.teamLead,
          progress: selectedProject.progress,
        } : null}
        onProjectUpdated={loadDashboardData}
      />
    </div>
  );
}

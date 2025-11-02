import { useState, useEffect } from 'react';
import { Upload, Users, Plus, Loader2, AlertCircle, X } from 'lucide-react';
import { Navbar } from '../../components/Navbar';
import { Sidebar } from '../../components/Sidebar';
import { TeamMemberCard } from '../../components/TeamMemberCard';

interface Project {
  _id: string;
  title: string;
}

interface TeamMemberData {
  id: string;
  name: string;
  email: string;
  role: string;
  phone?: string;
  techStack: string[];
  recentProjects: string[];
  experience?: string;
  avatar: string;
  initials: string;
  status: 'online' | 'offline' | 'busy';
}

export function TeamMembers() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [teamMembers, setTeamMembers] = useState<TeamMemberData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadTeamMembers();
    }
  }, [selectedProject]);

  const loadProjects = async () => {
    const token = localStorage.getItem('authToken');
    
    // Debug: Check token
    console.log('Loading projects with token:', token ? 'Token exists' : 'No token!');
    
    if (!token) {
      setError('Authentication required. Please log in again.');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/projects`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      console.log('Projects response status:', response.status);
      
      if (response.status === 401) {
        setError('Your session has expired. Please log in again.');
        return;
      }
      
      if (response.ok) {
        const data = await response.json();
        setProjects(data);
        if (data.length > 0 && !selectedProject) {
          setSelectedProject(data[0]._id);
        }
      }
    } catch (err) {
      console.error('Error loading projects:', err);
      setError('Failed to load projects');
    }
  };

  const loadTeamMembers = async () => {
    const token = localStorage.getItem('authToken');
    setIsLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/api/team-members/project/${selectedProject}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        
        // Transform data to match TeamMemberCard interface
        const transformedMembers = data.map((member: any) => ({
          id: member.id,
          name: member.name,
          email: member.email || 'No email',
          role: member.role,
          phone: member.phone,
          techStack: member.techStack || [],
          recentProjects: member.recentProjects || [],
          experience: member.experience,
          avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(member.name)}&background=random`,
          initials: member.name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2),
          status: 'online' as const
        }));
        
        setTeamMembers(transformedMembers);
      } else {
        setError('Failed to load team members');
      }
    } catch (err) {
      console.error('Error loading team members:', err);
      setError('Network error loading team members');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      // Validate file type
      const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
      if (!allowedTypes.includes(file.type)) {
        setError('Please upload a PDF, DOCX, or TXT file');
        return;
      }
      setSelectedFile(file);
      setError('');
    }
  };

  const handleUploadResume = async () => {
    if (!selectedFile || !selectedProject) {
      setError('Please select a file and project');
      return;
    }

    const token = localStorage.getItem('authToken');
    
    setIsUploading(true);
    setError('');
    setSuccessMessage('');

    try {
      console.log('Starting resume upload...', {
        file: selectedFile.name,
        project: selectedProject,
        token: token ? 'present' : 'missing'
      });

      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('project_id', selectedProject);

      const response = await fetch(`${API_BASE_URL}/api/team-members/upload-resume`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      console.log('Upload response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Upload successful:', data);
        setSuccessMessage(`Successfully added ${data.teamMember.name} to the team!`);
        setSelectedFile(null);
        setShowUploadModal(false);
        // Reload team members
        await loadTeamMembers();
        // Clear success message after 5 seconds
        setTimeout(() => setSuccessMessage(''), 5000);
      } else {
        const errorData = await response.json();
        console.error('Upload failed:', errorData);
        setError(errorData.detail || `Upload failed with status ${response.status}`);
      }
    } catch (err: any) {
      console.error('Error uploading resume:', err);
      setError(`Network error: ${err.message || 'Please check your connection and try again.'}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900">
      <Navbar />
      
      <div className="flex">
        <Sidebar />
        
        <main className="flex-1 p-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                    Team Members
                  </h1>
                  <p className="text-gray-600 dark:text-gray-300">
                    View and manage your team members
                  </p>
                </div>
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-semibold hover:shadow-lg transition-all duration-200"
                >
                  <Plus className="w-5 h-5" />
                  <span>Add Team Member</span>
                </button>
              </div>
            </div>

            {/* Project Selector */}
            <div className="mb-6 bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-4 border border-gray-200 dark:border-gray-700">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Select Project
              </label>
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="w-full p-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
              >
                {projects.length === 0 && <option value="">No projects available</option>}
                {projects.map((project) => (
                  <option key={project._id} value={project._id}>
                    {project.title}
                  </option>
                ))}
              </select>
            </div>

            {/* Success Message */}
            {successMessage && (
              <div className="mb-6 p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 flex items-center space-x-3">
                <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <p className="text-sm font-medium text-green-600 dark:text-green-400">{successMessage}</p>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 flex items-center space-x-3">
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0" />
                <p className="text-sm font-medium text-red-600 dark:text-red-400">{error}</p>
              </div>
            )}

            {/* Team Members Grid */}
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                <p className="ml-3 text-gray-600 dark:text-gray-300">Loading team members...</p>
              </div>
            ) : teamMembers.length === 0 ? (
              <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-12 text-center border border-gray-200 dark:border-gray-700">
                <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  No Team Members Yet
                </h3>
                <p className="text-gray-600 dark:text-gray-300 mb-4">
                  Upload resumes to add team members to this project
                </p>
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="inline-flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-semibold hover:shadow-lg transition-all duration-200"
                >
                  <Upload className="w-5 h-5" />
                  <span>Upload Resume</span>
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {teamMembers.map((member) => (
                  <TeamMemberCard key={member.id} member={member} />
                ))}
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md">
            {/* Modal Header */}
            <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">Upload Resume</h3>
              <button
                onClick={() => {
                  setShowUploadModal(false);
                  setSelectedFile(null);
                  setError('');
                }}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <X className="w-5 h-5 text-gray-600 dark:text-gray-300" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6">
              <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-8 text-center">
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                  Upload a resume (PDF, DOCX, or TXT)
                </p>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="resume-upload"
                />
                <label
                  htmlFor="resume-upload"
                  className="inline-block px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors cursor-pointer"
                >
                  Choose File
                </label>
                {selectedFile && (
                  <p className="mt-4 text-sm text-gray-700 dark:text-gray-300">
                    Selected: {selectedFile.name}
                  </p>
                )}
              </div>

              {error && (
                <div className="mt-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0" />
                  <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t border-gray-200 dark:border-gray-700">
              <div className="flex justify-end space-x-3 mb-4">
                <button
                  onClick={() => {
                    setShowUploadModal(false);
                    setSelectedFile(null);
                    setError('');
                  }}
                  className="px-4 py-2 rounded-lg font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                  disabled={isUploading}
                >
                  Cancel
                </button>
                <button
                  onClick={handleUploadResume}
                  disabled={!selectedFile || isUploading}
                  className="px-4 py-2 rounded-lg font-medium text-white bg-gradient-to-r from-blue-500 to-purple-500 hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Processing Resume with AI...</span>
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      <span>Upload & Process</span>
                    </>
                  )}
                </button>
              </div>

              {/* Progress Bar */}
              {isUploading && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      🤖 AI is extracting information...
                    </span>
                    <span className="text-sm text-blue-600 dark:text-blue-400 animate-pulse">
                      ⏳ Please wait
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
                    <div className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 h-full animate-pulse" style={{ width: '100%' }}></div>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                    📄 Extracting: Name • Skills • Experience • Projects • Education
                    <br />
                    <span className="text-blue-600 dark:text-blue-400 font-medium">This may take 10-30 seconds</span>
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

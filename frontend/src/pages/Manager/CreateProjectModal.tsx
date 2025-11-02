import React, { useState, useEffect } from 'react';
import { X, Calendar, User, FileText, Upload, AlertCircle } from 'lucide-react';

interface ProjectData {
  title: string;
  description: string;
  deadline: string;
  teamLeadId: string;
  files?: File[];
}

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (projectData: ProjectData) => void;
}

interface TeamLead {
  _id: string;
  name: string;
  email: string;
  isActive: boolean;
}

export function CreateProjectModal({ isOpen, onClose, onSubmit }: CreateProjectModalProps) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    deadline: '',
    teamLeadId: ''
  });
  const [teamLeads, setTeamLeads] = useState<TeamLead[]>([]);
  const [isLoadingLeads, setIsLoadingLeads] = useState(false);
  const [error, setError] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({});
  const [isUploading, setIsUploading] = useState(false);

  const token = localStorage.getItem('authToken');

  useEffect(() => {
    if (isOpen) {
      loadTeamLeads();
    }
  }, [isOpen]);

  const loadTeamLeads = async () => {
    setIsLoadingLeads(true);
    try {
      const response = await fetch('http://localhost:8000/api/auth/users/team-leads', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const leads = await response.json();
        setTeamLeads(leads.filter((lead: TeamLead) => lead.isActive));
      } else {
        setError('Failed to load team leads');
      }
    } catch (err) {
      console.error('Error loading team leads:', err);
      setError('Failed to load team leads');
    } finally {
      setIsLoadingLeads(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate form
    if (!formData.title || !formData.description || !formData.deadline) {
      setError('Please fill in all required fields');
      return;
    }

    // Call parent submit handler with form data and files
    await onSubmit({
      ...formData,
      files: selectedFiles.length > 0 ? selectedFiles : undefined
    });

    // Reset form
    setFormData({
      title: '',
      description: '',
      deadline: '',
      teamLeadId: ''
    });
    setSelectedFiles([]);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(files => files.filter((_, i) => i !== index));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl rounded-2xl sm:rounded-3xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-2xl my-8">
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white">
            Create New Project
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 sm:p-6 space-y-4">
          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start space-x-2">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          {/* Project Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Project Title *
            </label>
            <div className="relative">
              <FileText className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full pl-10 pr-4 py-2.5 sm:py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/50 dark:bg-gray-700/50 text-sm sm:text-base"
                placeholder="Enter project title"
                required
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Description *
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-2.5 sm:py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/50 dark:bg-gray-700/50 text-sm sm:text-base resize-none"
              rows={3}
              placeholder="Describe the project goals and requirements..."
              required
            />
          </div>

          {/* Deadline and Team Lead - Responsive Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Deadline */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Deadline *
              </label>
              <div className="relative">
                <Calendar className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2 pointer-events-none" />
                <input
                  type="date"
                  value={formData.deadline}
                  onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                  min={new Date().toISOString().split('T')[0]}
                  className="w-full pl-10 pr-4 py-2.5 sm:py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/50 dark:bg-gray-700/50 text-sm sm:text-base"
                  required
                />
              </div>
            </div>

            {/* Team Lead */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Assign Team Lead
              </label>
              <div className="relative">
                <User className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2 pointer-events-none" />
                <select
                  value={formData.teamLeadId}
                  onChange={(e) => setFormData({ ...formData, teamLeadId: e.target.value })}
                  disabled={isLoadingLeads}
                  className="w-full pl-10 pr-4 py-2.5 sm:py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/50 dark:bg-gray-700/50 text-sm sm:text-base appearance-none"
                >
                  <option value="">
                    {isLoadingLeads ? 'Loading...' : 'Optional - Assign later'}
                  </option>
                  {teamLeads.map((lead) => (
                    <option key={lead._id} value={lead._id}>
                      {lead.name} ({lead.email})
                    </option>
                  ))}
                </select>
              </div>
              {teamLeads.length === 0 && !isLoadingLeads && (
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  No team leads available. Add team leads first.
                </p>
              )}
            </div>
          </div>

          {/* Documents Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Documents (Optional)
            </label>
            <label 
              htmlFor="project-files" 
              className="block border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-4 sm:p-6 text-center cursor-pointer hover:bg-gray-50/50 dark:hover:bg-gray-700/30 transition-colors"
            >
              <Upload className="w-6 h-6 sm:w-8 sm:h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300">
                Click to upload or drag and drop
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                PDF, DOCX, TXT up to 10MB
              </p>
            </label>
            <input
              id="project-files"
              type="file"
              multiple
              accept=".pdf,.docx,.txt"
              className="hidden"
              onChange={handleFileChange}
            />
            
            {/* Selected Files */}
            {selectedFiles.length > 0 && (
              <div className="mt-3 space-y-2">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs sm:text-sm text-gray-700 dark:text-gray-300 truncate flex-1">
                        {file.name}
                      </span>
                      <button
                        type="button"
                        onClick={() => removeFile(index)}
                        className="ml-2 p-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                        disabled={isUploading}
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                    
                    {/* Progress Bar */}
                    {isUploading && (
                      <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
                          style={{ width: `${uploadProgress[file.name] || 0}%` }}
                        ></div>
                      </div>
                    )}
                    
                    {/* Upload Status */}
                    {isUploading && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {uploadProgress[file.name] === 100 ? 'Uploaded' : 'Uploading...'}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col-reverse sm:flex-row gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="w-full sm:flex-1 px-4 py-2.5 sm:py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm sm:text-base font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isUploading}
              className="w-full sm:flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-2.5 sm:py-3 rounded-xl font-medium hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg text-sm sm:text-base disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {isUploading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Creating Project...</span>
                </>
              ) : (
                'Create Project'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

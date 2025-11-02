import { useState, useEffect } from 'react';
import { X, Calendar, User, FileText, Upload, Trash2, Loader2, AlertCircle, Save } from 'lucide-react';

interface Document {
  id: string;
  filename: string;
  size: number;
  contentType: string;
  uploadedAt: string;
  uploadedBy: string;
}

interface TeamLead {
  _id: string;
  name: string;
}

interface Project {
  id: string;
  title: string;
  description: string;
  status: 'planning' | 'active' | 'completed' | 'on-hold' | 'cancelled';
  deadline: string;
  teamLeadId: string;
  teamLead: string;
  progress: number;
}

interface EditProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  project: Project | null;
  onProjectUpdated: () => void;
}

export function EditProjectModal({ isOpen, onClose, project, onProjectUpdated }: EditProjectModalProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [teamLeads, setTeamLeads] = useState<TeamLead[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [fileInputKey, setFileInputKey] = useState(Date.now());

  // Form fields
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [deadline, setDeadline] = useState('');
  const [status, setStatus] = useState<'planning' | 'active' | 'completed' | 'on-hold' | 'cancelled'>('active');
  const [teamLeadId, setTeamLeadId] = useState('');
  const [progress, setProgress] = useState(0);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const token = localStorage.getItem('authToken');

  useEffect(() => {
    if (isOpen && project) {
      // Initialize form with project data
      setTitle(project.title);
      setDescription(project.description);
      setDeadline(project.deadline.split('T')[0]); // Format for input[type="date"]
      setStatus(project.status);
      setTeamLeadId(project.teamLeadId);
      setProgress(project.progress);
      
      fetchDocuments();
      fetchTeamLeads();
    }
  }, [isOpen, project]);

  const fetchTeamLeads = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/users/team-leads`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setTeamLeads(data);
      }
    } catch (err) {
      console.error('Error fetching team leads:', err);
    }
  };

  const fetchDocuments = async () => {
    if (!project) return;
    
    setIsLoading(true);
    try {
      console.log('Fetching documents for project:', project.id);
      const response = await fetch(`${API_BASE_URL}/api/documents/project/${project.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Documents response:', data);
        if (data && Array.isArray(data.documents)) {
          console.log('Setting documents:', data.documents);
          setDocuments(data.documents);
        } else if (Array.isArray(data)) {
          console.log('Data is array directly:', data);
          setDocuments(data);
        } else {
          console.log('No documents found or unexpected format');
          setDocuments([]);
        }
      } else {
        console.error('Failed to fetch documents, status:', response.status);
      }
    } catch (err) {
      console.error('Error fetching documents:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const uploadNewDocuments = async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    setError('');

    try {
      const formData = new FormData();
      selectedFiles.forEach((file) => {
        formData.append('files', file);
      });

      console.log('Uploading documents to project:', project?.id);
      const response = await fetch(`${API_BASE_URL}/api/documents/upload/${project?.id}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Upload successful:', result);
        setSelectedFiles([]);
        setFileInputKey(Date.now()); // Force file input to re-render
        setUploadSuccess(true);
        setTimeout(() => setUploadSuccess(false), 3000); // Hide success message after 3s
        // Refresh document list
        await fetchDocuments();
      } else {
        const errorData = await response.json();
        console.error('Upload failed:', errorData);
        setError(errorData.detail || 'Failed to upload documents');
      }
    } catch (err) {
      console.error('Error uploading documents:', err);
      setError('Network error while uploading');
    } finally {
      setIsUploading(false);
    }
  };

  const deleteDocument = async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    setDeletingId(documentId);
    try {
      const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setDocuments((prev) => prev.filter((doc) => doc.id !== documentId));
      } else {
        setError('Failed to delete document');
      }
    } catch (err) {
      console.error('Error deleting document:', err);
      setError('Network error while deleting');
    } finally {
      setDeletingId(null);
    }
  };

  const handleSave = async () => {
    if (!project) return;

    setIsSaving(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/projects/${project.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title,
          description,
          deadline,
          status,
          teamLeadId,
          progress,
        }),
      });

      if (response.ok) {
        onProjectUpdated(); // Refresh parent component
        onClose();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to update project');
      }
    } catch (err) {
      console.error('Error updating project:', err);
      setError('Network error while saving');
    } finally {
      setIsSaving(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getFileIcon = (contentType: string) => {
    if (contentType.includes('pdf')) return '📄';
    if (contentType.includes('image')) return '🖼️';
    if (contentType.includes('word') || contentType.includes('document')) return '📝';
    if (contentType.includes('excel') || contentType.includes('spreadsheet')) return '📊';
    if (contentType.includes('powerpoint') || contentType.includes('presentation')) return '📽️';
    if (contentType.includes('zip') || contentType.includes('compressed')) return '📦';
    if (contentType.includes('text')) return '📃';
    return '📎';
  };

  if (!isOpen || !project) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm overflow-y-auto">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden my-8">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between sticky top-0 bg-white dark:bg-gray-800 z-10">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Edit Project</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <X className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-12rem)]">
          {error && (
            <div className="p-4 rounded-xl mb-4 flex items-center space-x-3 bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm font-medium">{error}</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Title */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Project Title *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* Description */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description *
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* Deadline */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Calendar className="w-4 h-4 inline mr-1" />
                Deadline *
              </label>
              <input
                type="date"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* Team Lead */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <User className="w-4 h-4 inline mr-1" />
                Assign to Team Lead *
              </label>
              <select
                value={teamLeadId}
                onChange={(e) => setTeamLeadId(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select Team Lead</option>
                {teamLeads.map((lead) => (
                  <option key={lead._id} value={lead._id}>
                    {lead.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Project Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as any)}
                className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="planning">Planning</option>
                <option value="active">Active</option>
                <option value="on-hold">On Hold</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            {/* Progress */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Progress: {progress}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={progress}
                onChange={(e) => setProgress(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
              />
            </div>
          </div>

          {/* Documents Section */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
              <FileText className="w-5 h-5" />
              <span>Project Documents</span>
              {documents.length > 0 && (
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  ({documents.length} {documents.length === 1 ? 'file' : 'files'})
                </span>
              )}
            </h3>

            {/* Upload New Documents */}
            <div className="mb-4 p-4 rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Upload className="w-4 h-4 inline mr-1" />
                Add New Documents
              </label>
              <input
                key={fileInputKey}
                type="file"
                multiple
                onChange={handleFileChange}
                className="w-full text-sm text-gray-600 dark:text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 dark:file:bg-blue-900/30 dark:file:text-blue-400"
              />
              {uploadSuccess && (
                <div className="mt-3 p-3 rounded-lg bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 flex items-center space-x-2">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm font-medium">Documents uploaded successfully!</span>
                </div>
              )}
              {selectedFiles.length > 0 && (
                <div className="mt-3">
                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                    Selected: {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''}
                  </p>
                  <button
                    onClick={uploadNewDocuments}
                    disabled={isUploading}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                  >
                    {isUploading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Uploading...</span>
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4" />
                        <span>Upload Files</span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>

            {/* Existing Documents */}
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                <p className="ml-3 text-gray-600 dark:text-gray-300">Loading documents...</p>
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                <p className="text-sm text-gray-500 dark:text-gray-400">No documents uploaded yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-700/50 hover:shadow-md transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3 flex-1 min-w-0">
                        <span className="text-2xl flex-shrink-0">{getFileIcon(doc.contentType)}</span>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-gray-900 dark:text-white truncate text-sm">
                            {doc.filename}
                          </h4>
                          <div className="flex items-center space-x-2 mt-1 text-xs text-gray-500 dark:text-gray-400">
                            <span>{formatFileSize(doc.size)}</span>
                            <span>•</span>
                            <span>{formatDate(doc.uploadedAt)}</span>
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => deleteDocument(doc.id)}
                        disabled={deletingId === doc.id}
                        className="ml-4 p-2 rounded-lg bg-red-100 hover:bg-red-200 dark:bg-red-900/30 dark:hover:bg-red-900/50 text-red-600 dark:text-red-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Delete document"
                      >
                        {deletingId === doc.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 flex items-center justify-end space-x-3 sticky bottom-0">
          <button
            onClick={onClose}
            className="px-6 py-3 rounded-xl font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || !title || !description || !deadline || !teamLeadId}
            className="px-6 py-3 rounded-xl font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Saving...</span>
              </>
            ) : (
              <>
                <Save className="w-5 h-5" />
                <span>Save Changes</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}


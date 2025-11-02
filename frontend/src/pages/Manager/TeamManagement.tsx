import React, { useState, useEffect } from 'react';
import { Plus, Trash2, UserPlus, Mail, Lock, User as UserIcon, CheckCircle, XCircle } from 'lucide-react';
import { Navbar } from '../../components/Navbar';

interface TeamLead {
  _id: string;
  name: string;
  email: string;
  role: string;
  initials: string;
  isActive: boolean;
  createdAt: string;
  lastLogin: string | null;
}

interface AddLeadFormData {
  name: string;
  email: string;
  password: string;
}

export function TeamManagement() {
  const [teamLeads, setTeamLeads] = useState<TeamLead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [formData, setFormData] = useState<AddLeadFormData>({
    name: '',
    email: '',
    password: ''
  });

  const token = localStorage.getItem('authToken');

  useEffect(() => {
    fetchTeamLeads();
  }, []);

  const fetchTeamLeads = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/auth/users/team-leads', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setTeamLeads(data);
      } else {
        setError('Failed to fetch team leads');
      }
    } catch (err) {
      setError('Network error while fetching team leads');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddLead = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      // First fetch current user to get startupId
      const meResponse = await fetch('http://localhost:8000/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!meResponse.ok) {
        setError('Failed to get user information');
        return;
      }

      const userData = await meResponse.json();
      
      const response = await fetch('http://localhost:8000/api/auth/users/add-lead', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ...formData,
          role: 'teamlead',
          startupId: userData.startupId
        }),
      });

      if (response.ok) {
        setSuccess('Team lead added successfully!');
        setFormData({ name: '', email: '', password: '' });
        setShowAddModal(false);
        fetchTeamLeads();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to add team lead');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
  };

  const handleRemoveLead = async (userId: string, userName: string) => {
    if (!confirm(`Are you sure you want to remove ${userName} from your team?`)) {
      return;
    }

    setError('');
    setSuccess('');

    try {
      const response = await fetch(`http://localhost:8000/api/auth/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setSuccess('Team lead removed successfully!');
        fetchTeamLeads();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to remove team lead');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
  };

  const handleActivateLead = async (userId: string, userName: string) => {
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`http://localhost:8000/api/auth/users/${userId}/activate`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setSuccess(`${userName} has been reactivated!`);
        fetchTeamLeads();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to activate user');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900">
      <Navbar />
      
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                Team Lead Management
              </h1>
              <p className="text-gray-600 dark:text-gray-300">
                Add, remove, and manage team leads in your organization
              </p>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl font-medium hover:from-blue-700 hover:to-purple-700 transition-all duration-200 flex items-center space-x-2 shadow-lg"
            >
              <Plus className="w-5 h-5" />
              <span>Add Team Lead</span>
            </button>
          </div>

          {/* Notifications */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-600 dark:text-red-400 flex items-center justify-between">
              <span>{error}</span>
              <button onClick={() => setError('')} className="text-red-600 dark:text-red-400 hover:text-red-800">
                <XCircle className="w-5 h-5" />
              </button>
            </div>
          )}

          {success && (
            <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl text-green-600 dark:text-green-400 flex items-center justify-between">
              <span className="flex items-center space-x-2">
                <CheckCircle className="w-5 h-5" />
                <span>{success}</span>
              </span>
              <button onClick={() => setSuccess('')} className="text-green-600 dark:text-green-400 hover:text-green-800">
                <XCircle className="w-5 h-5" />
              </button>
            </div>
          )}

          {/* Team Leads List */}
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-300">Loading team leads...</p>
            </div>
          ) : teamLeads.length === 0 ? (
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-12 text-center">
              <UserPlus className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                No Team Leads Yet
              </h3>
              <p className="text-gray-600 dark:text-gray-300 mb-6">
                Get started by adding your first team lead
              </p>
              <button
                onClick={() => setShowAddModal(true)}
                className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl font-medium hover:from-blue-700 hover:to-purple-700 transition-all duration-200"
              >
                Add Team Lead
              </button>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {teamLeads.map((lead) => (
                <div
                  key={lead._id}
                  className={`bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg p-6 ${
                    !lead.isActive ? 'opacity-60' : ''
                  }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                        <span className="text-white font-semibold">{lead.initials}</span>
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                          {lead.name}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-300">Team Lead</p>
                      </div>
                    </div>
                    {lead.isActive ? (
                      <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded-full">
                        Active
                      </span>
                    ) : (
                      <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-400 text-xs rounded-full">
                        Inactive
                      </span>
                    )}
                  </div>

                  <div className="space-y-2 mb-4">
                    <div className="flex items-center text-sm text-gray-600 dark:text-gray-300">
                      <Mail className="w-4 h-4 mr-2" />
                      {lead.email}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      Added: {new Date(lead.createdAt).toLocaleDateString()}
                    </div>
                    {lead.lastLogin && (
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        Last login: {new Date(lead.lastLogin).toLocaleDateString()}
                      </div>
                    )}
                  </div>

                  <div className="flex gap-2">
                    {lead.isActive ? (
                      <button
                        onClick={() => handleRemoveLead(lead._id, lead.name)}
                        className="flex-1 px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors flex items-center justify-center space-x-2"
                      >
                        <Trash2 className="w-4 h-4" />
                        <span className="text-sm font-medium">Remove</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => handleActivateLead(lead._id, lead.name)}
                        className="flex-1 px-4 py-2 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/40 transition-colors flex items-center justify-center space-x-2"
                      >
                        <CheckCircle className="w-4 h-4" />
                        <span className="text-sm font-medium">Activate</span>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add Team Lead Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl rounded-3xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-md">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Add New Team Lead
              </h2>
            </div>

            <form onSubmit={handleAddLead} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Full Name *
                </label>
                <div className="relative">
                  <UserIcon className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/50 dark:bg-gray-700/50"
                    placeholder="John Doe"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Email Address *
                </label>
                <div className="relative">
                  <Mail className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/50 dark:bg-gray-700/50"
                    placeholder="john@company.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Password *
                </label>
                <div className="relative">
                  <Lock className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/50 dark:bg-gray-700/50"
                    placeholder="Minimum 8 characters"
                  />
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddModal(false);
                    setFormData({ name: '', email: '', password: '' });
                    setError('');
                  }}
                  className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-3 rounded-xl font-medium hover:from-blue-700 hover:to-purple-700 transition-all duration-200"
                >
                  Add Team Lead
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


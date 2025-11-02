import { useState, useRef, useEffect } from 'react';
import { 
  User, 
  Settings, 
  HelpCircle, 
  LogOut, 
  ChevronDown,
  Shield,
  Building
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export function ProfileDropdown() {
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getRoleBadgeColor = (role: string | undefined) => {
    if (role === 'manager') {
      return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400';
    }
    return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
  };

  const getRoleIcon = (role: string | undefined) => {
    if (role === 'manager') {
      return <Building className="w-3 h-3" />;
    }
    return <Shield className="w-3 h-3" />;
  };

  const getRoleDisplayName = (role: string | undefined) => {
    if (role === 'manager') return 'Manager';
    if (role === 'teamlead') return 'Team Lead';
    return role;
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-3 p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 group"
      >
        {/* Avatar */}
        <div className="relative">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center ring-2 ring-white dark:ring-gray-800 group-hover:ring-blue-200 dark:group-hover:ring-blue-800 transition-all">
            <span className="text-sm font-bold text-white">
              {user?.initials}
            </span>
          </div>
          <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white dark:border-gray-800 rounded-full"></div>
        </div>

        {/* User Info */}
        <div className="hidden md:block text-left">
          <p className="text-sm font-semibold text-gray-900 dark:text-white leading-tight">
            {user?.name}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {user?.email}
          </p>
        </div>

        {/* Dropdown Icon */}
        <ChevronDown className={`w-4 h-4 text-gray-500 dark:text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200">
          {/* Header */}
          <div className="p-4 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                <span className="text-base font-bold text-white">
                  {user?.initials}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold text-gray-900 dark:text-white truncate">
                  {user?.name}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-300 truncate">
                  {user?.email}
                </p>
                {/* Role Badge */}
                <div className="flex items-center space-x-1 mt-1.5">
                  <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold ${getRoleBadgeColor(user?.role)}`}>
                    {getRoleIcon(user?.role)}
                    <span>{getRoleDisplayName(user?.role)}</span>
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Menu Items */}
          <div className="py-2">
            <button
              onClick={() => {
                setIsOpen(false);
                // Navigate to profile page when implemented
              }}
              className="w-full px-4 py-3 flex items-center space-x-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors text-left"
            >
              <User className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">My Profile</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">View and edit profile</p>
              </div>
            </button>

            <button
              onClick={() => {
                setIsOpen(false);
                // Navigate to settings page when implemented
              }}
              className="w-full px-4 py-3 flex items-center space-x-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors text-left"
            >
              <Settings className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">Settings</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Account preferences</p>
              </div>
            </button>

            <button
              onClick={() => {
                setIsOpen(false);
                // Open help/support when implemented
              }}
              className="w-full px-4 py-3 flex items-center space-x-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors text-left"
            >
              <HelpCircle className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">Help & Support</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Get assistance</p>
              </div>
            </button>
          </div>

          {/* Logout */}
          <div className="border-t border-gray-200 dark:border-gray-700 p-2">
            <button
              onClick={handleLogout}
              className="w-full px-4 py-3 flex items-center space-x-3 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors rounded-lg text-left group"
            >
              <LogOut className="w-4 h-4 text-red-600 dark:text-red-400" />
              <div>
                <p className="text-sm font-medium text-red-600 dark:text-red-400">Sign Out</p>
                <p className="text-xs text-red-500 dark:text-red-400/70">Logout from your account</p>
              </div>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}


import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

const Layout = ({ children }) => {
  const { user, logout, isSuperAdmin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Role-based menu items
  const getMenuItems = () => {
    const role = user?.role;
    
    if (role === 'SUPER_ADMIN') {
      return [
        { id: 'dashboard', label: 'Dashboard', icon: '📊', path: '/dashboard' },
        { id: 'schools', label: 'Schools', icon: '🏫', path: '/dashboard/schools' },
        { id: 'create-school', label: 'Create School', icon: '➕', path: '/dashboard/create-school' },
        { id: 'admins', label: 'Admins', icon: '👥', path: '/dashboard/admins' },
        { id: 'create-admin', label: 'Create Admin', icon: '➕', path: '/dashboard/create-admin' },
        { id: 'users', label: 'All Users', icon: '👤', path: '/dashboard/users' },
      ];
    } else if (role === 'ADMIN') {
      return [
        { id: 'dashboard', label: 'Dashboard', icon: '📊', path: '/dashboard' },
        { id: 'school', label: 'My School', icon: '🏫', path: '/dashboard/school' },
        { id: 'teachers', label: 'Teachers', icon: '👨‍🏫', path: '/dashboard/teachers' },
        { id: 'students', label: 'Students', icon: '👨‍🎓', path: '/dashboard/students' },
        { id: 'parents', label: 'Parents', icon: '👨‍👩‍👧', path: '/dashboard/parents' },
      ];
    } else if (role === 'TEACHER') {
      return [
        { id: 'dashboard', label: 'Dashboard', icon: '📊', path: '/dashboard' },
        { id: 'classes', label: 'My Classes', icon: '📚', path: '/dashboard/classes' },
        { id: 'students', label: 'Students', icon: '👨‍🎓', path: '/dashboard/students' },
        { id: 'attendance', label: 'Attendance', icon: '✅', path: '/dashboard/attendance' },
      ];
    } else if (role === 'PARENT') {
      return [
        { id: 'dashboard', label: 'Dashboard', icon: '📊', path: '/dashboard' },
        { id: 'children', label: 'My Children', icon: '👨‍👩‍👧', path: '/dashboard/children' },
        { id: 'grades', label: 'Grades', icon: '📝', path: '/dashboard/grades' },
        { id: 'attendance', label: 'Attendance', icon: '✅', path: '/dashboard/attendance' },
      ];
    } else if (role === 'STUDENT') {
      return [
        { id: 'dashboard', label: 'Dashboard', icon: '📊', path: '/dashboard' },
        { id: 'grades', label: 'My Grades', icon: '📝', path: '/dashboard/grades' },
        { id: 'attendance', label: 'Attendance', icon: '✅', path: '/dashboard/attendance' },
        { id: 'schedule', label: 'Schedule', icon: '📅', path: '/dashboard/schedule' },
      ];
    }
    
    // Default menu for unknown roles
    return [
      { id: 'dashboard', label: 'Dashboard', icon: '📊', path: '/dashboard' },
    ];
  };

  const menuItems = getMenuItems();

  const handleNavigation = (path) => {
    navigate(path);
  };

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const getRoleDisplayName = (role) => {
    const roleNames = {
      'SUPER_ADMIN': 'Super Admin',
      'ADMIN': 'School Admin',
      'TEACHER': 'Teacher',
      'PARENT': 'Parent',
      'STUDENT': 'Student',
    };
    return roleNames[role] || role;
  };

  const getDashboardTitle = (role) => {
    const titles = {
      'SUPER_ADMIN': 'Super Admin Dashboard',
      'ADMIN': 'School Admin Dashboard',
      'TEACHER': 'Teacher Dashboard',
      'PARENT': 'Parent Dashboard',
      'STUDENT': 'Student Dashboard',
    };
    return titles[role] || 'Dashboard';
  };

  const getDashboardSubtitle = (role) => {
    const subtitles = {
      'SUPER_ADMIN': 'Manage schools, admins, and users',
      'ADMIN': 'Manage your school',
      'TEACHER': 'Manage your classes and students',
      'PARENT': 'View your children\'s information',
      'STUDENT': 'View your academic information',
    };
    return subtitles[role] || 'Welcome to your dashboard';
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'w-64' : 'w-20'
        } bg-gray-900 text-white transition-all duration-300 fixed h-full flex flex-col`}
      >
        {/* Logo */}
        <div className="p-6 border-b border-gray-700 flex-shrink-0">
          <div className="flex items-center justify-between">
            {sidebarOpen && (
              <h1 className="text-xl font-bold text-white">School Management</h1>
            )}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-lg hover:bg-gray-800 transition"
            >
              {sidebarOpen ? '◀' : '▶'}
            </button>
          </div>
        </div>

        {/* User Info */}
        <div className="p-4 border-b border-gray-700 flex-shrink-0">
          {sidebarOpen ? (
            <div>
              <p className="text-sm text-gray-400">Logged in as</p>
              <p className="text-sm font-semibold text-white mt-1">{getRoleDisplayName(user?.role)}</p>
            </div>
          ) : (
            <div className="flex justify-center">
              <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center text-xs font-bold">
                {user?.role?.charAt(0) || 'A'}
              </div>
            </div>
          )}
        </div>

        {/* Navigation Menu - Scrollable */}
        <nav className="flex-1 overflow-y-auto p-4 space-y-2">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleNavigation(item.path)}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                isActive(item.path)
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              {sidebarOpen && <span className="font-medium">{item.label}</span>}
            </button>
          ))}
        </nav>

        {/* Logout Button - Fixed at bottom */}
        <div className="p-4 border-t border-gray-700 flex-shrink-0">
          <button
            onClick={logout}
            className="w-full flex items-center justify-center space-x-3 px-4 py-3 rounded-lg bg-red-600 hover:bg-red-700 text-white transition"
          >
            <span>🚪</span>
            {sidebarOpen && <span className="font-medium">Logout</span>}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className={`flex-1 ${sidebarOpen ? 'ml-64' : 'ml-20'} transition-all duration-300`}>
        {/* Top Header */}
        <header className="bg-white shadow-sm border-b sticky top-0 z-10">
          <div className="px-6 py-4">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-gray-800">{getDashboardTitle(user?.role)}</h2>
                <p className="text-sm text-gray-600">{getDashboardSubtitle(user?.role)}</p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-800">{user?.email || 'User'}</p>
                  <p className="text-xs text-gray-500">{getRoleDisplayName(user?.role)}</p>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
};

export default Layout;

import React, { useState, useEffect } from 'react';
import { teacherAPI } from '../../services/api';

const TeacherDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await teacherAPI.getDashboardStats();
      setStats(data);
      setError('');
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load dashboard statistics. Please try again.';
      setError(`Failed to load dashboard statistics: ${errorMessage}`);
      console.error('Error fetching stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon, color }) => (
    <div className="bg-white rounded-lg shadow-md p-6 border-l-4" style={{ borderLeftColor: color }}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
        </div>
        <div className="text-4xl opacity-20" style={{ color }}>
          {icon}
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        <p className="mt-4 text-gray-600">Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-800">{error}</p>
        <button
          onClick={fetchStats}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm font-medium"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Teacher Dashboard</h1>
        <button
          onClick={fetchStats}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm font-medium"
        >
          Refresh
        </button>
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="My Classes"
          value={stats?.total_classes || 0}
          icon="📚"
          color="#4F46E5"
        />
        <StatCard
          title="Total Students"
          value={stats?.total_students || 0}
          icon="👨‍🎓"
          color="#10B981"
        />
        <StatCard
          title="Total Lessons"
          value={stats?.total_lessons || 0}
          icon="📖"
          color="#F59E0B"
        />
        <StatCard
          title="Upcoming Lessons"
          value={stats?.upcoming_lessons || 0}
          icon="📅"
          color="#EF4444"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => window.location.href = '/dashboard/classes'}
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition text-left"
          >
            <div className="text-2xl mb-2">📚</div>
            <div className="font-medium text-gray-800">View My Classes</div>
            <div className="text-sm text-gray-600 mt-1">See all your assigned classes</div>
          </button>
          <button
            onClick={() => window.location.href = '/dashboard/students'}
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition text-left"
          >
            <div className="text-2xl mb-2">👨‍🎓</div>
            <div className="font-medium text-gray-800">View Students</div>
            <div className="text-sm text-gray-600 mt-1">Manage your students</div>
          </button>
          <button
            onClick={() => window.location.href = '/dashboard/attendance'}
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition text-left"
          >
            <div className="text-2xl mb-2">✅</div>
            <div className="font-medium text-gray-800">Mark Attendance</div>
            <div className="text-sm text-gray-600 mt-1">Take attendance for your classes</div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default TeacherDashboard;


import React, { useState, useEffect } from 'react';
import { schoolAdminAPI } from '../../services/api';

const SchoolAdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await schoolAdminAPI.getDashboardStats();
      setStats(data);
      setError('');
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load dashboard statistics. Please try again.';
      setError(`Failed to load dashboard statistics: ${errorMessage}`);
      console.error('Error fetching stats:', err);
      console.error('Error response:', err.response);
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
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">School Admin Dashboard</h1>
        <p className="text-gray-600 mt-2">Overview of your school management</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Teachers"
          value={stats?.total_teachers || 0}
          icon="👨‍🏫"
          color="#3B82F6"
        />
        <StatCard
          title="Total Students"
          value={stats?.total_students || 0}
          icon="👨‍🎓"
          color="#10B981"
        />
        <StatCard
          title="Total Parents"
          value={stats?.total_parents || 0}
          icon="👨‍👩‍👧"
          color="#F59E0B"
        />
        <StatCard
          title="Total Classes"
          value={stats?.total_classes || 0}
          icon="📚"
          color="#8B5CF6"
        />
        <StatCard
          title="Total Lessons"
          value={stats?.total_lessons || 0}
          icon="📖"
          color="#EC4899"
        />
        <StatCard
          title="Today's Classes"
          value={stats?.todays_classes || 0}
          icon="📅"
          color="#06B6D4"
        />
        <StatCard
          title="Upcoming Holidays"
          value={stats?.upcoming_holidays || 0}
          icon="🎉"
          color="#F97316"
        />
        <StatCard
          title="Upcoming Events"
          value={stats?.upcoming_events || 0}
          icon="📢"
          color="#14B8A6"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a
            href="/dashboard/teachers"
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition"
          >
            <div className="text-2xl mb-2">👨‍🏫</div>
            <div className="font-semibold text-gray-800">Manage Teachers</div>
            <div className="text-sm text-gray-600">Add or upload teachers</div>
          </a>
          <a
            href="/dashboard/students"
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition"
          >
            <div className="text-2xl mb-2">👨‍🎓</div>
            <div className="font-semibold text-gray-800">Manage Students</div>
            <div className="text-sm text-gray-600">Add or upload students</div>
          </a>
          <a
            href="/dashboard/parents"
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition"
          >
            <div className="text-2xl mb-2">👨‍👩‍👧</div>
            <div className="font-semibold text-gray-800">Manage Parents</div>
            <div className="text-sm text-gray-600">Add or upload parents</div>
          </a>
        </div>
      </div>
    </div>
  );
};

export default SchoolAdminDashboard;

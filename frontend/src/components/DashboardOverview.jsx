import React, { useState, useEffect } from 'react';
import { dashboardAPI } from '../services/api';

const DashboardOverview = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await dashboardAPI.getStats();
      setStats(data);
      setError('');
    } catch (err) {
      setError('Failed to load statistics. Please try again.');
      console.error('Error fetching stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon, color }) => (
    <div className="bg-white rounded-lg shadow p-6 border-l-4" style={{ borderLeftColor: color }}>
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
        <p className="mt-4 text-gray-600">Loading statistics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard Overview</h1>
        <button
          onClick={fetchStats}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm font-medium"
        >
          Refresh
        </button>
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard
          title="Total Schools"
          value={stats?.total_schools || 0}
          icon="🏫"
          color="#4F46E5"
        />
        <StatCard
          title="Total Admins"
          value={stats?.total_admins || 0}
          icon="👥"
          color="#10B981"
        />
        <StatCard
          title="Total Users"
          value={stats?.total_users || 0}
          icon="👤"
          color="#F59E0B"
        />
        <StatCard
          title="Teachers"
          value={stats?.total_teachers || 0}
          icon="👨‍🏫"
          color="#3B82F6"
        />
        <StatCard
          title="Students"
          value={stats?.total_students || 0}
          icon="🎓"
          color="#8B5CF6"
        />
        <StatCard
          title="Parents"
          value={stats?.total_parents || 0}
          icon="👨‍👩‍👧"
          color="#EC4899"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => window.location.href = '/dashboard/create-school'}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition text-left"
          >
            <div className="text-2xl mb-2">➕</div>
            <div className="font-medium text-gray-800">Create School</div>
            <div className="text-sm text-gray-500">Add a new school</div>
          </button>
          <button
            onClick={() => window.location.href = '/dashboard/create-admin'}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition text-left"
          >
            <div className="text-2xl mb-2">👥</div>
            <div className="font-medium text-gray-800">Create Admin</div>
            <div className="text-sm text-gray-500">Add a new admin</div>
          </button>
          <button
            onClick={() => window.location.href = '/dashboard/schools'}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition text-left"
          >
            <div className="text-2xl mb-2">🏫</div>
            <div className="font-medium text-gray-800">View Schools</div>
            <div className="text-sm text-gray-500">Manage all schools</div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default DashboardOverview;

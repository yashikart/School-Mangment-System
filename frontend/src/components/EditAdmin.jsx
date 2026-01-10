import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { adminsAPI, schoolsAPI } from '../services/api';

const EditAdmin = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [schools, setSchools] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    school_id: '',
  });
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      setFetching(true);
      const [admin, schoolsData] = await Promise.all([
        adminsAPI.getById(id),
        schoolsAPI.getAll()
      ]);
      
      setSchools(schoolsData);
      setFormData({
        name: admin.name || '',
        email: admin.email || '',
        password: '', // Don't pre-fill password
        school_id: admin.school_id || '',
      });
    } catch (err) {
      setError('Failed to load admin details.');
      console.error('Error fetching admin:', err);
    } finally {
      setFetching(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const updateData = {};
      if (formData.name) updateData.name = formData.name;
      if (formData.email) updateData.email = formData.email;
      if (formData.password) updateData.password = formData.password;
      if (formData.school_id) updateData.school_id = parseInt(formData.school_id);

      await adminsAPI.update(id, updateData);
      setSuccess('Admin updated successfully!');
      setTimeout(() => {
        navigate('/dashboard/admins');
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update admin. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        <p className="mt-4 text-gray-600">Loading admin details...</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-semibold text-gray-800">Edit Admin</h2>
          <p className="text-sm text-indigo-600 font-medium mt-1">Admin ID: {id}</p>
        </div>
        <button
          onClick={() => navigate('/dashboard/admins')}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition text-sm font-medium"
        >
          Cancel
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-800 text-sm">{success}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
            Admin Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
          />
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
            Email Address <span className="text-red-500">*</span>
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
            New Password
          </label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            minLength="6"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
            placeholder="Leave empty to keep current password"
          />
          <p className="mt-1 text-sm text-gray-500">
            Leave empty if you don't want to change the password
          </p>
        </div>

        <div>
          <label htmlFor="school_id" className="block text-sm font-medium text-gray-700 mb-2">
            School (School ID)
          </label>
          <select
            id="school_id"
            name="school_id"
            value={formData.school_id}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
          >
            <option value="">-- Select a school --</option>
            {schools.map((school) => (
              <option key={school.id} value={school.id}>
                {school.name} (School ID: {school.id})
              </option>
            ))}
          </select>
          {formData.school_id && (
            <p className="mt-1 text-xs text-indigo-600">
              Selected: School ID {formData.school_id}
            </p>
          )}
        </div>

        <div className="flex space-x-4">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-indigo-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Updating...' : 'Update Admin'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/dashboard/admins')}
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditAdmin;

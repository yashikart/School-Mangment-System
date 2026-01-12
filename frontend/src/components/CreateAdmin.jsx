import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { adminsAPI, schoolsAPI } from '../services/api';

const CreateAdmin = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const selectedSchoolId = searchParams.get('schoolId');
  
  const [schools, setSchools] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    school_id: selectedSchoolId || '',
  });
  const [loading, setLoading] = useState(false);
  const [fetchingSchools, setFetchingSchools] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchSchools();
    if (selectedSchoolId) {
      setFormData(prev => ({ ...prev, school_id: selectedSchoolId }));
    }
  }, [selectedSchoolId]);

  const fetchSchools = async () => {
    try {
      setFetchingSchools(true);
      const data = await schoolsAPI.getAll();
      setSchools(data);
    } catch (err) {
      setError('Failed to load schools. Please try again.');
      console.error('Error fetching schools:', err);
    } finally {
      setFetchingSchools(false);
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

    if (!formData.school_id) {
      setError('Please select a school');
      setLoading(false);
      return;
    }

    try {
      await adminsAPI.invite(formData);
      setSuccess(`Admin invitation sent to ${formData.email}! The admin will receive an email to set their password.`);
      setFormData({ name: '', email: '', school_id: selectedSchoolId || '' });
      
      setTimeout(() => {
        navigate('/dashboard/admins');
      }, 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to invite admin. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 max-w-2xl mx-auto">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">Invite School Admin</h2>
      <p className="text-sm text-gray-600 mb-6">
        Invite an admin by email. They will receive a secure link to set their own password.
      </p>

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
          <label htmlFor="school_id" className="block text-sm font-medium text-gray-700 mb-2">
            Select School (School ID) <span className="text-red-500">*</span>
          </label>
          <select
            id="school_id"
            name="school_id"
            value={formData.school_id}
            onChange={handleChange}
            required
            disabled={fetchingSchools || !!selectedSchoolId}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none disabled:bg-gray-100"
          >
            <option value="">-- Select a school --</option>
            {schools.map((school) => (
              <option key={school.id} value={school.id}>
                {school.name} (School ID: {school.id})
              </option>
            ))}
          </select>
          {selectedSchoolId && (
            <p className="mt-1 text-sm text-indigo-600 font-medium">
              ✓ School pre-selected: School ID {selectedSchoolId} from Schools list
            </p>
          )}
          {formData.school_id && !selectedSchoolId && (
            <p className="mt-1 text-xs text-indigo-600">
              Selected: School ID {formData.school_id}
            </p>
          )}
        </div>

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
            placeholder="Enter admin name"
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
            placeholder="admin@example.com"
          />
        </div>


        <div className="flex space-x-4">
          <button
            type="submit"
            disabled={loading || !formData.school_id}
            className="flex-1 bg-indigo-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Sending Invitation...' : 'Send Invitation'}
          </button>
          <button
            type="button"
            onClick={() => setFormData({ name: '', email: '', school_id: selectedSchoolId || '' })}
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition"
          >
            Clear
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateAdmin;

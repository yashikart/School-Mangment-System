import React, { useState, useEffect } from 'react';
import { schoolAdminAPI } from '../../services/api';

const TeachersManagement = () => {
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  
  // Create form state
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: ''
  });
  const [editingTeacher, setEditingTeacher] = useState(null);

  useEffect(() => {
    fetchTeachers();
  }, [searchTerm]);

  const fetchTeachers = async () => {
    try {
      setLoading(true);
      const data = await schoolAdminAPI.getTeachers(searchTerm || null);
      setTeachers(data);
      setError('');
    } catch (err) {
      setError('Failed to load teachers. Please try again.');
      console.error('Error fetching teachers:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTeacher = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.createTeacher(formData);
      setShowCreateForm(false);
      setFormData({ name: '', email: '', subject: '' });
      fetchTeachers();
      alert('Teacher created successfully! Login credentials sent via email.');
    } catch (err) {
      console.error('Error creating teacher:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to create teacher. Please check the console for details.';
      alert(`Error: ${errorMessage}`);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      alert('Please upload an Excel file (.xlsx or .xls)');
      return;
    }

    try {
      const result = await schoolAdminAPI.uploadTeachersExcel(file);
      setUploadResult(result);
      fetchTeachers();
      if (result.failed_count > 0) {
        alert(`Upload completed with ${result.failed_count} failures. Check details below.`);
      } else {
        alert('All teachers uploaded successfully!');
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to upload file');
    }
  };

  const handleEdit = (teacher) => {
    setEditingTeacher(teacher);
    setFormData({
      name: teacher.name,
      email: teacher.email,
      subject: teacher.subject || ''
    });
    setShowCreateForm(true);
  };

  const handleUpdateTeacher = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.updateTeacher(editingTeacher.id, {
        name: formData.name,
        email: formData.email,
        subject: formData.subject
      });
      setShowCreateForm(false);
      setEditingTeacher(null);
      setFormData({ name: '', email: '', subject: '' });
      fetchTeachers();
      alert('Teacher updated successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update teacher');
    }
  };

  const handleDelete = async (teacherId) => {
    if (!window.confirm('Are you sure you want to delete this teacher? This action cannot be undone.')) {
      return;
    }
    try {
      await schoolAdminAPI.deleteTeacher(teacherId);
      fetchTeachers();
      alert('Teacher deleted successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete teacher');
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        <p className="mt-4 text-gray-600">Loading teachers...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Teachers Management</h1>
          <p className="text-gray-600 mt-2">Manage all teachers in your school</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowUploadForm(!showUploadForm)}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
          >
            📤 Upload Excel
          </button>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
          >
            ➕ Add Teacher
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <input
          type="text"
          placeholder="Search teachers by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
      </div>

      {/* Upload Form */}
      {showUploadForm && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Upload Teachers from Excel</h2>
          <p className="text-sm text-gray-600 mb-4">
            Excel file should have columns: <strong>name</strong>, <strong>email</strong>, <strong>subject</strong> (optional)
          </p>
          <input
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileUpload}
            className="mb-4"
          />
          {uploadResult && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="font-semibold">Upload Result:</p>
              <p>✅ Success: {uploadResult.success_count}</p>
              <p>❌ Failed: {uploadResult.failed_count}</p>
              {uploadResult.failed_rows && uploadResult.failed_rows.length > 0 && (
                <div className="mt-2">
                  <p className="font-semibold">Failed Rows:</p>
                  <ul className="list-disc list-inside text-sm">
                    {uploadResult.failed_rows.map((row, idx) => (
                      <li key={idx}>
                        Row {row.row}: {row.email} - {row.reason}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Create Form */}
      {showCreateForm && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">
            {editingTeacher ? 'Edit Teacher' : 'Create New Teacher'}
          </h2>
          <form onSubmit={editingTeacher ? handleUpdateTeacher : handleCreateTeacher} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email *</label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Subject</label>
              <input
                type="text"
                value={formData.subject}
                onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
              >
                {editingTeacher ? 'Update Teacher' : 'Create Teacher'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  setEditingTeacher(null);
                  setFormData({ name: '', email: '', subject: '' });
                }}
                className="px-4 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Teachers List */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-800">All Teachers ({teachers.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {teachers.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-4 text-center text-gray-500">
                    No teachers found
                  </td>
                </tr>
              ) : (
                teachers.map((teacher) => (
                  <tr key={teacher.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{teacher.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{teacher.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{teacher.email}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{teacher.subject || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(teacher)}
                          className="text-indigo-600 hover:text-indigo-900 transition"
                          title="Edit"
                        >
                          ✏️ Edit
                        </button>
                        <button
                          onClick={() => handleDelete(teacher.id)}
                          className="text-red-600 hover:text-red-900 transition"
                          title="Delete"
                        >
                          🗑️ Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TeachersManagement;

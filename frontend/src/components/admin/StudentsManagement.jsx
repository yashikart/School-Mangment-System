import React, { useState, useEffect } from 'react';
import { schoolAdminAPI } from '../../services/api';

const StudentsManagement = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    grade: '',
    parent_email: '',
    parent_name: ''
  });
  const [editingStudent, setEditingStudent] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);

  useEffect(() => {
    fetchStudents();
  }, [searchTerm]);

  const fetchStudents = async () => {
    try {
      setLoading(true);
      const data = await schoolAdminAPI.getStudents(searchTerm || null);
      setStudents(data);
      setError('');
    } catch (err) {
      setError('Failed to load students. Please try again.');
      console.error('Error fetching students:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateStudent = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.createStudent(formData);
      setShowCreateForm(false);
      setFormData({ name: '', email: '', grade: '', parent_email: '', parent_name: '' });
      fetchStudents();
      alert('Student created successfully! Login credentials sent via email.');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create student');
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
      const result = await schoolAdminAPI.uploadStudentsExcel(file);
      setUploadResult(result);
      fetchStudents();
      if (result.failed_count > 0) {
        alert(`Upload completed with ${result.failed_count} failures. Check details below.`);
      } else {
        alert('All students uploaded successfully!');
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to upload file');
    }
  };

  const handleEdit = (student) => {
    setEditingStudent(student);
      setFormData({
        name: student.name,
        email: student.email,
        grade: student.grade || '',
        parent_email: '',
        parent_name: ''
      });
    setShowCreateForm(true);
  };

  const handleUpdateStudent = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.updateStudent(editingStudent.id, {
        name: formData.name,
        email: formData.email,
        grade: formData.grade
      });
      setShowCreateForm(false);
      setEditingStudent(null);
      setFormData({ name: '', email: '', grade: '', parent_email: '', parent_name: '' });
      fetchStudents();
      alert('Student updated successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update student');
    }
  };

  const handleDelete = async (studentId) => {
    if (!window.confirm('Are you sure you want to delete this student? This action cannot be undone.')) {
      return;
    }
    try {
      await schoolAdminAPI.deleteStudent(studentId);
      fetchStudents();
      alert('Student deleted successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete student');
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        <p className="mt-4 text-gray-600">Loading students...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Students Management</h1>
          <p className="text-gray-600 mt-2">Manage all students in your school</p>
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
            ➕ Add Student
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-4">
        <input
          type="text"
          placeholder="Search students by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {showUploadForm && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Upload Students from Excel</h2>
          <p className="text-sm text-gray-600 mb-4">
            Excel file should have columns: <strong>name</strong>, <strong>email</strong>, <strong>grade</strong> (optional), <strong>parent_email</strong> (optional)
          </p>
          <input type="file" accept=".xlsx,.xls" onChange={handleFileUpload} className="mb-4" />
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
                      <li key={idx}>Row {row.row}: {row.email} - {row.reason}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {showCreateForm && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">
            {editingStudent ? 'Edit Student' : 'Create New Student'}
          </h2>
          <form onSubmit={editingStudent ? handleUpdateStudent : handleCreateStudent} className="space-y-4">
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
              <label className="block text-sm font-medium text-gray-700 mb-2">Grade</label>
              <input
                type="text"
                value={formData.grade}
                onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            {!editingStudent && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Parent Name</label>
                  <input
                    type="text"
                    value={formData.parent_name}
                    onChange={(e) => setFormData({ ...formData, parent_name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="Optional: Parent's name (if creating new parent)"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Parent Email</label>
                  <input
                    type="email"
                    value={formData.parent_email}
                    onChange={(e) => setFormData({ ...formData, parent_email: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="Optional: Link to existing parent or create new"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    If parent email exists, it will link to existing parent. If not, a new parent will be created.
                  </p>
                </div>
              </>
            )}
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
              >
                {editingStudent ? 'Update Student' : 'Create Student'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  setEditingStudent(null);
                  setFormData({ name: '', email: '', grade: '', parent_email: '', parent_name: '' });
                }}
                className="px-4 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-800">All Students ({students.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grade</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Parent Email(s)</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {students.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                    No students found
                  </td>
                </tr>
              ) : (
                students.map((student) => (
                  <tr key={student.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{student.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{student.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{student.email}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{student.grade || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {student.parent_emails && Array.isArray(student.parent_emails) && student.parent_emails.length > 0 ? (
                        <div className="flex flex-col gap-1">
                          {student.parent_emails.map((email, idx) => {
                            const parentName = student.parent_names && student.parent_names[idx] ? student.parent_names[idx] : '';
                            return (
                              <span key={idx} className="inline-flex items-center px-2 py-1 rounded-md bg-green-100 text-green-800 text-xs font-medium">
                                <span className="mr-1">✓</span> 
                                {parentName && <span className="font-semibold mr-1">{parentName}</span>}
                                <span className="text-gray-600">({email})</span>
                              </span>
                            );
                          })}
                        </div>
                      ) : (
                        <span className="text-gray-400 italic">No parent linked</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(student)}
                          className="text-indigo-600 hover:text-indigo-900 transition"
                          title="Edit"
                        >
                          ✏️ Edit
                        </button>
                        <button
                          onClick={() => handleDelete(student.id)}
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

export default StudentsManagement;

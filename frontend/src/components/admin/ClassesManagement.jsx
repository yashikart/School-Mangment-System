import React, { useState, useEffect } from 'react';
import { schoolAdminAPI } from '../../services/api';

const ClassesManagement = () => {
  const [classes, setClasses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showCreateSubjectForm, setShowCreateSubjectForm] = useState(false);
  const [selectedClass, setSelectedClass] = useState(null);
  const [classStudents, setClassStudents] = useState({}); // { classId: [students] }
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assigningClassId, setAssigningClassId] = useState(null);
  const [subjectFormData, setSubjectFormData] = useState({
    name: '',
    code: ''
  });

  const [formData, setFormData] = useState({
    name: '',
    grade: '',
    subject_id: '',
    teacher_id: '',
    academic_year: '',
  });

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [classesData, subjectsData, teachersData, studentsData] = await Promise.all([
        schoolAdminAPI.getClasses(),
        schoolAdminAPI.getSubjects(),
        schoolAdminAPI.getTeachers(),
        schoolAdminAPI.getStudents(),
      ]);
      setClasses(classesData);
      setSubjects(subjectsData || []);
      setTeachers(teachersData || []);
      setStudents(studentsData || []);
      setError('');
      
      // Fetch students for each class
      const studentsMap = {};
      for (const cls of classesData) {
        try {
          const enrolledStudents = await schoolAdminAPI.getClassStudents(cls.id);
          studentsMap[cls.id] = enrolledStudents;
        } catch (err) {
          console.error(`Error fetching students for class ${cls.id}:`, err);
          studentsMap[cls.id] = [];
        }
      }
      setClassStudents(studentsMap);
      
      // Show warning if no subjects exist
      if (!subjectsData || subjectsData.length === 0) {
        setError('No subjects found. Please create subjects first before creating classes.');
      }
    } catch (err) {
      console.error('Error fetching classes data:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load classes. Please try again.';
      setError(`Error: ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSubject = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.createSubject({
        name: subjectFormData.name,
        code: subjectFormData.code || null,
      });
      setShowCreateSubjectForm(false);
      setSubjectFormData({ name: '', code: '' });
      fetchInitialData();
      alert('Subject created successfully!');
    } catch (err) {
      console.error('Error creating subject:', err);
      alert(err.response?.data?.detail || 'Failed to create subject');
    }
  };

  const handleCreateClass = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.createClass({
        name: formData.name,
        grade: formData.grade,
        subject_id: parseInt(formData.subject_id, 10),
        teacher_id: parseInt(formData.teacher_id, 10),
        academic_year: formData.academic_year || null,
      });
      setShowCreateForm(false);
      setFormData({
        name: '',
        grade: '',
        subject_id: '',
        teacher_id: '',
        academic_year: '',
      });
      fetchInitialData();
      alert('Class created successfully!');
    } catch (err) {
      console.error('Error creating class:', err);
      alert(err.response?.data?.detail || 'Failed to create class');
    }
  };

  const handleAssignStudent = async (classId, studentId) => {
    try {
      await schoolAdminAPI.assignStudentToClass(classId, studentId);
      // Refresh class students
      const enrolledStudents = await schoolAdminAPI.getClassStudents(classId);
      setClassStudents({ ...classStudents, [classId]: enrolledStudents });
      setShowAssignModal(false);
      setAssigningClassId(null);
      alert('Student assigned to class successfully!');
      fetchInitialData(); // Refresh to update counts
    } catch (err) {
      console.error('Error assigning student:', err);
      alert(err.response?.data?.detail || 'Failed to assign student to class');
    }
  };

  const handleRemoveStudent = async (classId, studentId) => {
    if (!window.confirm('Are you sure you want to remove this student from the class?')) {
      return;
    }
    try {
      await schoolAdminAPI.removeStudentFromClass(classId, studentId);
      // Refresh class students
      const enrolledStudents = await schoolAdminAPI.getClassStudents(classId);
      setClassStudents({ ...classStudents, [classId]: enrolledStudents });
      alert('Student removed from class successfully!');
      fetchInitialData(); // Refresh to update counts
    } catch (err) {
      console.error('Error removing student:', err);
      alert(err.response?.data?.detail || 'Failed to remove student from class');
    }
  };

  const openAssignModal = (classId) => {
    setAssigningClassId(classId);
    setShowAssignModal(true);
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        <p className="mt-4 text-gray-600">Loading classes...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Classes Management</h1>
          <p className="text-gray-600 mt-2">Manage classes, subjects, and teachers</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowCreateSubjectForm(!showCreateSubjectForm)}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
          >
            ➕ Create Subject
          </button>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
          >
            ➕ Create Class
          </button>
        </div>
      </div>

      {/* Create Subject Form */}
      {showCreateSubjectForm && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Create New Subject</h2>
          <form onSubmit={handleCreateSubject} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Subject Name *</label>
              <input
                type="text"
                required
                value={subjectFormData.name}
                onChange={(e) => setSubjectFormData({ ...subjectFormData, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                placeholder="e.g., Mathematics"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Subject Code (Optional)</label>
              <input
                type="text"
                value={subjectFormData.code}
                onChange={(e) => setSubjectFormData({ ...subjectFormData, code: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                placeholder="e.g., MATH"
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
              >
                Create Subject
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateSubjectForm(false);
                  setSubjectFormData({ name: '', code: '' });
                }}
                className="px-4 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {showCreateForm && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Create New Class</h2>
          <form onSubmit={handleCreateClass} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Class Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                placeholder="e.g., Grade 5A"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Grade *</label>
              <input
                type="text"
                required
                value={formData.grade}
                onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                placeholder="e.g., 5"
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Subject *</label>
                <select
                  required
                  value={formData.subject_id}
                  onChange={(e) => setFormData({ ...formData, subject_id: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  disabled={subjects.length === 0}
                >
                  <option value="">
                    {subjects.length === 0 ? 'No subjects available. Create subjects first.' : 'Select subject'}
                  </option>
                  {subjects.map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.name} {subject.code ? `(${subject.code})` : ''}
                    </option>
                  ))}
                </select>
                {subjects.length === 0 && (
                  <p className="mt-1 text-sm text-red-600">
                    No subjects found. Click "Create Subject" button above to add subjects.
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Teacher *</label>
                <select
                  required
                  value={formData.teacher_id}
                  onChange={(e) => setFormData({ ...formData, teacher_id: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select teacher</option>
                  {teachers.map((teacher) => (
                    <option key={teacher.id} value={teacher.id}>
                      {teacher.name} ({teacher.email})
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Academic Year</label>
              <input
                type="text"
                value={formData.academic_year}
                onChange={(e) => setFormData({ ...formData, academic_year: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                placeholder="e.g., 2024-2025"
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
              >
                Create Class
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
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
          <h2 className="text-xl font-bold text-gray-800">All Classes ({classes.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grade</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Teacher</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Students</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Academic Year</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {classes.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                    No classes found
                  </td>
                </tr>
              ) : (
                classes.map((cls) => {
                  const enrolledStudents = classStudents[cls.id] || [];
                  const isExpanded = selectedClass === cls.id;
                  return (
                    <React.Fragment key={cls.id}>
                      <tr className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{cls.id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{cls.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{cls.grade}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {cls.subject_name || `Subject #${cls.subject_id}`}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {cls.teacher_name || `Teacher #${cls.teacher_id}`}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className="font-semibold">{enrolledStudents.length}</span> enrolled
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {cls.academic_year || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div className="flex gap-2">
                            <button
                              onClick={() => setSelectedClass(isExpanded ? null : cls.id)}
                              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-xs"
                            >
                              {isExpanded ? '▼ Hide' : '▶ View'} Students
                            </button>
                            <button
                              onClick={() => openAssignModal(cls.id)}
                              className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-xs"
                            >
                              ➕ Assign
                            </button>
                          </div>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan="7" className="px-6 py-4 bg-gray-50">
                            <div className="space-y-2">
                              <h4 className="font-semibold text-gray-700">Enrolled Students ({enrolledStudents.length}):</h4>
                              {enrolledStudents.length === 0 ? (
                                <p className="text-gray-500 text-sm">No students enrolled yet. Click "Assign" to add students.</p>
                              ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                                  {enrolledStudents.map((student) => (
                                    <div key={student.id} className="flex items-center justify-between bg-white p-2 rounded border">
                                      <div>
                                        <span className="font-medium text-sm">{student.name}</span>
                                        <span className="text-xs text-gray-500 ml-2">({student.email})</span>
                                      </div>
                                      <button
                                        onClick={() => handleRemoveStudent(cls.id, student.id)}
                                        className="px-2 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-xs"
                                      >
                                        Remove
                                      </button>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Assign Student Modal */}
      {showAssignModal && assigningClassId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gray-800 mb-4">Assign Student to Class</h2>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {students
                .filter(student => {
                  // Filter out students already enrolled in this class
                  const enrolled = classStudents[assigningClassId] || [];
                  return !enrolled.some(s => s.id === student.id);
                })
                .map((student) => (
                  <div key={student.id} className="flex items-center justify-between p-3 border rounded hover:bg-gray-50">
                    <div>
                      <span className="font-medium">{student.name}</span>
                      <span className="text-sm text-gray-500 ml-2">({student.email})</span>
                      {student.grade && (
                        <span className="text-xs text-gray-400 ml-2">Grade: {student.grade}</span>
                      )}
                    </div>
                    <button
                      onClick={() => handleAssignStudent(assigningClassId, student.id)}
                      className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
                    >
                      Assign
                    </button>
                  </div>
                ))}
              {students.filter(student => {
                const enrolled = classStudents[assigningClassId] || [];
                return !enrolled.some(s => s.id === student.id);
              }).length === 0 && (
                <p className="text-gray-500 text-center py-4">All students are already assigned to this class.</p>
              )}
            </div>
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => {
                  setShowAssignModal(false);
                  setAssigningClassId(null);
                }}
                className="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClassesManagement;


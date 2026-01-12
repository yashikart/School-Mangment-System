import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle 401 errors (unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid, clear it and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/auth/login-json', { email, password });
    return response.data;
  },
  setPassword: async (token, password) => {
    const response = await api.post('/auth/set-password', { token, password });
    return response.data;
  },
};

// Schools API
export const schoolsAPI = {
  getAll: async (search = null) => {
    const params = search ? { search } : {};
    const response = await api.get('/schools/', { params });
    return response.data;
  },
  getById: async (schoolId) => {
    const response = await api.get(`/schools/${schoolId}`);
    return response.data;
  },
  create: async (schoolData) => {
    const response = await api.post('/schools/', schoolData);
    return response.data;
  },
  update: async (schoolId, schoolData) => {
    const response = await api.put(`/schools/${schoolId}`, schoolData);
    return response.data;
  },
  delete: async (schoolId) => {
    await api.delete(`/schools/${schoolId}`);
    return true;
  },
};

// Admins API
export const adminsAPI = {
  getAll: async (search = null, schoolId = null) => {
    const params = {};
    if (search) params.search = search;
    if (schoolId) params.school_id = schoolId;
    const response = await api.get('/schools/admins', { params });
    return response.data;
  },
  getById: async (adminId) => {
    const response = await api.get(`/schools/admins/${adminId}`);
    return response.data;
  },
  getBySchool: async (schoolId) => {
    const response = await api.get(`/schools/${schoolId}/admins`);
    return response.data;
  },
  // Invite admin via email (new email-based flow)
  invite: async (adminData) => {
    const response = await api.post('/super/invite-admin', {
      name: adminData.name,
      email: adminData.email,
      school_id: parseInt(adminData.school_id)
    });
    return response.data;
  },
  // Legacy create endpoint (still available but not recommended)
  create: async (schoolId, adminData) => {
    const response = await api.post(`/schools/${schoolId}/admins`, adminData);
    return response.data;
  },
  update: async (adminId, adminData) => {
    const response = await api.put(`/schools/admins/${adminId}`, adminData);
    return response.data;
  },
  delete: async (adminId) => {
    await api.delete(`/schools/admins/${adminId}`);
    return true;
  },
};

// Dashboard API
export const dashboardAPI = {
  getStats: async () => {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },
  getUsers: async (search = null, role = null, schoolId = null) => {
    const params = {};
    if (search) params.search = search;
    if (role) params.role = role;
    if (schoolId) params.school_id = schoolId;
    const response = await api.get('/dashboard/users', { params });
    return response.data;
  },
  getUserById: async (userId) => {
    const response = await api.get(`/dashboard/users/${userId}`);
    return response.data;
  },
};

// School Admin API
export const schoolAdminAPI = {
  // Dashboard Stats
  getDashboardStats: async () => {
    const response = await api.get('/admin/dashboard/stats');
    return response.data;
  },
  
  // Teachers
  getTeachers: async (search = null) => {
    const params = {};
    if (search) params.search = search;
    const response = await api.get('/admin/teachers', { params });
    return response.data;
  },
  createTeacher: async (teacherData) => {
    const response = await api.post('/admin/teachers', teacherData);
    return response.data;
  },
  updateTeacher: async (teacherId, teacherData) => {
    const response = await api.put(`/admin/teachers/${teacherId}`, teacherData);
    return response.data;
  },
  deleteTeacher: async (teacherId) => {
    const response = await api.delete(`/admin/teachers/${teacherId}`);
    return response.data;
  },
  uploadTeachersExcel: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/admin/teachers/upload-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  // Students
  getStudents: async (search = null, grade = null) => {
    const params = {};
    if (search) params.search = search;
    if (grade) params.grade = grade;
    const response = await api.get('/admin/students', { params });
    return response.data;
  },
  createStudent: async (studentData) => {
    const response = await api.post('/admin/students', studentData);
    return response.data;
  },
  updateStudent: async (studentId, studentData) => {
    const response = await api.put(`/admin/students/${studentId}`, studentData);
    return response.data;
  },
  deleteStudent: async (studentId) => {
    const response = await api.delete(`/admin/students/${studentId}`);
    return response.data;
  },
  uploadStudentsExcel: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/admin/students/upload-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  // Parents
  getParents: async (search = null) => {
    const params = {};
    if (search) params.search = search;
    const response = await api.get('/admin/parents', { params });
    return response.data;
  },
  createParent: async (parentData) => {
    const response = await api.post('/admin/parents', parentData);
    return response.data;
  },
  updateParent: async (parentId, parentData) => {
    const response = await api.put(`/admin/parents/${parentId}`, parentData);
    return response.data;
  },
  deleteParent: async (parentId) => {
    const response = await api.delete(`/admin/parents/${parentId}`);
    return response.data;
  },
  uploadParentsExcel: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/admin/parents/upload-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  // Subjects
  getSubjects: async () => {
    const response = await api.get('/admin/subjects');
    return response.data;
  },
  createSubject: async (subjectData) => {
    const response = await api.post('/admin/subjects', subjectData);
    return response.data;
  },
  
  // Classes
  getClasses: async () => {
    const response = await api.get('/admin/classes');
    return response.data;
  },
  createClass: async (classData) => {
    const response = await api.post('/admin/classes', classData);
    return response.data;
  },
  assignStudentToClass: async (classId, studentId) => {
    const response = await api.post(`/admin/classes/${classId}/students/${studentId}`);
    return response.data;
  },
  getClassStudents: async (classId) => {
    const response = await api.get(`/admin/classes/${classId}/students`);
    return response.data;
  },
  removeStudentFromClass: async (classId, studentId) => {
    const response = await api.delete(`/admin/classes/${classId}/students/${studentId}`);
    return response.data;
  },
  
  // Timetable
  getTimetable: async (classId = null) => {
    const params = {};
    if (classId) params.class_id = classId;
    const response = await api.get('/admin/timetable', { params });
    return response.data;
  },
  createTimetableSlot: async (slotData) => {
    const response = await api.post('/admin/timetable', slotData);
    return response.data;
  },
  
  // Holidays
  getHolidays: async () => {
    const response = await api.get('/admin/holidays');
    return response.data;
  },
  createHoliday: async (holidayData) => {
    const response = await api.post('/admin/holidays', holidayData);
    return response.data;
  },
  
  // Events
  getEvents: async () => {
    const response = await api.get('/admin/events');
    return response.data;
  },
  createEvent: async (eventData) => {
    const response = await api.post('/admin/events', eventData);
    return response.data;
  },
  
  // Announcements
  getAnnouncements: async (targetAudience = null) => {
    const params = {};
    if (targetAudience) params.target_audience = targetAudience;
    const response = await api.get('/admin/announcements', { params });
    return response.data;
  },
  createAnnouncement: async (announcementData) => {
    const response = await api.post('/admin/announcements', announcementData);
    return response.data;
  },
  
  // Lessons
  getLessons: async (classId = null) => {
    const params = {};
    if (classId) params.class_id = classId;
    const response = await api.get('/admin/lessons', { params });
    return response.data;
  },
  
  // Parent-Student Mapping
  getStudentParents: async (studentId) => {
    const response = await api.get(`/admin/students/${studentId}/parents`);
    return response.data;
  },
  getParentStudents: async (parentId) => {
    const response = await api.get(`/admin/parents/${parentId}/students`);
    return response.data;
  },
  createParentStudentLink: async (linkData) => {
    const response = await api.post('/admin/parent-student/link', linkData);
    return response.data;
  },
  deleteParentStudentLink: async (linkId) => {
    const response = await api.delete(`/admin/parent-student/link/${linkId}`);
    return response.data;
  },
  getStudentsWithParents: async (search = null) => {
    const params = search ? { search } : {};
    const response = await api.get('/admin/students-with-parents', { params });
    return response.data;
  },
  getParentsWithStudents: async (search = null) => {
    const params = search ? { search } : {};
    const response = await api.get('/admin/parents-with-students', { params });
    return response.data;
  },
  getParentStudentStats: async () => {
    const response = await api.get('/admin/parent-student/stats');
    return response.data;
  },
  uploadStudentsParentsCombined: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/admin/parent-student/upload-combined-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  // Analytics
  getAnalytics: async () => {
    const response = await api.get('/admin/analytics');
    return response.data;
  },
};

export default api;

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

export default api;

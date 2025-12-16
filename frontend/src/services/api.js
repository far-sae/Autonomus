import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (email, password) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    const response = await axios.post(`${API_BASE_URL}/api/v1/auth/login`, formData);
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/api/v1/auth/me');
    return response.data;
  },
  
  register: async (userData) => {
    const response = await api.post('/api/v1/auth/register', userData);
    return response.data;
  },
};

// Organizations API
export const organizationsAPI = {
  getAll: async () => {
    const response = await api.get('/api/v1/organizations');
    return response.data;
  },
  
  getById: async (id) => {
    const response = await api.get(`/api/v1/organizations/${id}`);
    return response.data;
  },
  
  create: async (orgData) => {
    const response = await api.post('/api/v1/organizations', orgData);
    return response.data;
  },
};

// Cloud Accounts API
export const cloudAccountsAPI = {
  getAll: async (organizationId = null) => {
    const params = organizationId ? { organization_id: organizationId } : {};
    const response = await api.get('/api/v1/cloud-accounts', { params });
    return response.data;
  },
  
  create: async (accountData) => {
    const response = await api.post('/api/v1/cloud-accounts', accountData);
    return response.data;
  },
};

// Scans API
export const scansAPI = {
  runScan: async (accountId, controlIds = null) => {
    const response = await api.post('/api/v1/scans', {
      account_id: accountId,
      control_ids: controlIds,
    });
    return response.data;
  },
  
  getComplianceScore: async (accountId = null, organizationId = null) => {
    const params = {};
    if (accountId) params.account_id = accountId;
    if (organizationId) params.organization_id = organizationId;
    const response = await api.get('/api/v1/compliance-score', { params });
    return response.data;
  },
};

// Findings API
export const findingsAPI = {
  getAll: async (filters = {}) => {
    const response = await api.get('/api/v1/findings', { params: filters });
    return response.data;
  },
};

// Remediation API
export const remediationAPI = {
  remediate: async (findingId, dryRun = true, approvedBy = null) => {
    const response = await api.post('/api/v1/remediations', {
      finding_id: findingId,
      dry_run: dryRun,
      approved_by: approvedBy,
    });
    return response.data;
  },
  
  rollback: async (findingId) => {
    const response = await api.post(`/api/v1/remediations/${findingId}/rollback`);
    return response.data;
  },
};

// Audit API
export const auditAPI = {
  generateReport: async (organizationId, format = 'pdf', startDate = null, endDate = null) => {
    const response = await api.post('/api/v1/audit-reports', {
      organization_id: organizationId,
      format,
      start_date: startDate,
      end_date: endDate,
    });
    return response.data;
  },
  
  getAuditLogs: async (filters = {}) => {
    const response = await api.get('/api/v1/audit-logs', { params: filters });
    return response.data;
  },
};

// Health check
export const healthAPI = {
  check: async () => {
    const response = await axios.get(`${API_BASE_URL}/health`);
    return response.data;
  },
};

export default api;

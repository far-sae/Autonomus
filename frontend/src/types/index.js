// Constants and utility types for the Compliance Platform

// Severity levels
export const SEVERITY_LEVELS = {
  CRITICAL: 'critical',
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
};

// Status types
export const STATUS_TYPES = {
  PASS: 'PASS',
  FAIL: 'FAIL',
  FIXED: 'FIXED',
  ERROR: 'ERROR',
  MANUAL: 'MANUAL',
};

// User roles
export const USER_ROLES = {
  ADMIN: 'admin',
  USER: 'user',
  AUDITOR: 'auditor',
};

// Cloud providers
export const CLOUD_PROVIDERS = {
  AWS: 'aws',
  AZURE: 'azure',
  M365: 'm365',
};

export const SEVERITY_COLORS = {
  critical: '#d32f2f',
  high: '#f57c00',
  medium: '#fbc02d',
  low: '#689f38',
};

export const STATUS_COLORS = {
  PASS: '#4caf50',
  FAIL: '#f44336',
  FIXED: '#2196f3',
  ERROR: '#ff9800',
  MANUAL: '#9e9e9e',
};

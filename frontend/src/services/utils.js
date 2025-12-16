// Utility helper functions

export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString();
};

export const formatRelativeTime = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minutes ago`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} hours ago`;
  
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays} days ago`;
  
  return formatDate(dateString);
};

export const truncateText = (text, maxLength = 50) => {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

export const getComplianceGrade = (score) => {
  if (score >= 95) return 'A+';
  if (score >= 90) return 'A';
  if (score >= 85) return 'B+';
  if (score >= 80) return 'B';
  if (score >= 75) return 'C+';
  if (score >= 70) return 'C';
  if (score >= 60) return 'D';
  return 'F';
};

export const getSeverityWeight = (severity) => {
  const weights = {
    critical: 4,
    high: 3,
    medium: 2,
    low: 1,
  };
  return weights[severity] || 0;
};

export const sortBySeverity = (findings) => {
  return [...findings].sort((a, b) => 
    getSeverityWeight(b.severity) - getSeverityWeight(a.severity)
  );
};

export const groupByStatus = (findings) => {
  return findings.reduce((acc, finding) => {
    const status = finding.status;
    if (!acc[status]) acc[status] = [];
    acc[status].push(finding);
    return acc;
  }, {});
};

export const groupBySeverity = (findings) => {
  return findings.reduce((acc, finding) => {
    const severity = finding.severity;
    if (!acc[severity]) acc[severity] = [];
    acc[severity].push(finding);
    return acc;
  }, {});
};

export const calculateRiskScore = (findings) => {
  if (!findings || findings.length === 0) return 0;
  
  const severityScores = {
    critical: 10,
    high: 7,
    medium: 4,
    low: 1,
  };
  
  const totalScore = findings.reduce((sum, finding) => {
    if (finding.status === 'FAIL') {
      return sum + (severityScores[finding.severity] || 0);
    }
    return sum;
  }, 0);
  
  return Math.min(100, Math.round(totalScore));
};

export const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

export const exportToCSV = (data, filename = 'export.csv') => {
  if (!data || data.length === 0) return;
  
  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => JSON.stringify(row[header] || '')).join(',')
    )
  ].join('\n');
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
};

export const downloadJSON = (data, filename = 'export.json') => {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
};

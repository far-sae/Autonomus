import React, { useState, useEffect } from 'react';
import {
  Container, Grid, Paper, Typography, Box, Button, Alert,
  Select, MenuItem, FormControl, InputLabel
} from '@mui/material';
import { Refresh, GetApp, PlayArrow } from '@mui/icons-material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import ComplianceScoreCard from '../components/ComplianceScoreCard';
import FindingsTable from '../components/FindingsTable';
import { scansAPI, findingsAPI, cloudAccountsAPI, remediationAPI, auditAPI } from '../services/api';
import { SEVERITY_COLORS } from '../types';

const Dashboard = ({ user, onLogout }) => {
  const [complianceScore, setComplianceScore] = useState(null);
  const [findings, setFindings] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    loadAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      loadData();
    }
  }, [selectedAccount]);

  const loadAccounts = async () => {
    try {
      const data = await cloudAccountsAPI.getAll();
      setAccounts(data);
      if (data.length > 0) {
        setSelectedAccount(data[0].id);
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load accounts' });
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [score, findingsData] = await Promise.all([
        scansAPI.getComplianceScore(selectedAccount),
        findingsAPI.getAll({ account_id: selectedAccount, status: 'FAIL' })
      ]);
      setComplianceScore(score);
      setFindings(findingsData);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load data' });
    } finally {
      setLoading(false);
    }
  };

  const handleRunScan = async () => {
    if (!selectedAccount) return;
    setLoading(true);
    setMessage({ type: 'info', text: 'Running scan...' });
    try {
      await scansAPI.runScan(selectedAccount);
      setMessage({ type: 'success', text: 'Scan completed successfully' });
      await loadData();
    } catch (error) {
      setMessage({ type: 'error', text: 'Scan failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleRemediate = async (findingId) => {
    try {
      const result = await remediationAPI.remediate(findingId, false, user.email);
      if (result.success) {
        setMessage({ type: 'success', text: 'Remediation successful' });
        await loadData();
      } else {
        setMessage({ type: 'error', text: result.message || 'Remediation failed' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Remediation failed' });
    }
  };

  const handleExportReport = async () => {
    try {
      setMessage({ type: 'info', text: 'Generating report...' });
      const result = await auditAPI.generateReport(1, 'pdf');
      window.open(result.download_url, '_blank');
      setMessage({ type: 'success', text: 'Report generated successfully' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to generate report' });
    }
  };

  const getPieData = () => {
    if (!complianceScore) return [];
    return [
      { name: 'Passed', value: complianceScore.pass },
      { name: 'Failed', value: complianceScore.fail },
      { name: 'Fixed', value: complianceScore.fixed },
    ];
  };

  const getSeverityData = () => {
    const severityCounts = { critical: 0, high: 0, medium: 0, low: 0 };
    findings.forEach(f => {
      severityCounts[f.severity] = (severityCounts[f.severity] || 0) + 1;
    });
    return Object.entries(severityCounts).map(([name, value]) => ({ name, value }));
  };

  const PIE_COLORS = ['#4caf50', '#f44336', '#2196f3'];

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Compliance Dashboard</Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            {user?.email}
          </Typography>
          <Button variant="outlined" onClick={onLogout}>Logout</Button>
        </Box>
      </Box>

      {message && (
        <Alert severity={message.type} onClose={() => setMessage(null)} sx={{ mb: 2 }}>
          {message.text}
        </Alert>
      )}

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <FormControl fullWidth>
            <InputLabel>Cloud Account</InputLabel>
            <Select
              value={selectedAccount}
              label="Cloud Account"
              onChange={(e) => setSelectedAccount(e.target.value)}
            >
              {accounts.map((acc) => (
                <MenuItem key={acc.id} value={acc.id}>
                  {acc.name} ({acc.provider})
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} md={8} sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
          <Button 
            variant="contained" 
            startIcon={<PlayArrow />}
            onClick={handleRunScan}
            disabled={loading || !selectedAccount}
          >
            Run Scan
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<Refresh />}
            onClick={loadData}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<GetApp />}
            onClick={handleExportReport}
          >
            Export Report
          </Button>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <ComplianceScoreCard score={complianceScore} />
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Status Distribution</Typography>
            {complianceScore && (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={getPieData()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {getPieData().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Severity Breakdown</Typography>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={getSeverityData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8884d8">
                  {getSeverityData().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={SEVERITY_COLORS[entry.name]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Failed Findings</Typography>
            <FindingsTable 
              findings={findings} 
              onRemediate={handleRemediate}
            />
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;

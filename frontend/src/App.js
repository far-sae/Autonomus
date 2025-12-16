import React, { useState, useEffect } from 'react';
import { Container, AppBar, Toolbar, Typography, Box, Grid, Card, CardContent, Button, 
         Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
         Chip, CircularProgress, Alert, Dialog, DialogTitle, DialogContent, DialogActions,
         TextField, Select, MenuItem, FormControl, InputLabel, Tab, Tabs } from '@mui/material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const COLORS = { PASS: '#4caf50', FAIL: '#f44336', FIXED: '#2196f3', ERROR: '#ff9800' };
const SEVERITY_COLORS = { critical: '#d32f2f', high: '#f57c00', medium: '#fbc02d', low: '#689f38' };

function App() {
  const [score, setScore] = useState(null);
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [scanLoading, setScanLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [showAddAccount, setShowAddAccount] = useState(false);
  const [newAccount, setNewAccount] = useState({
    name: '',
    provider: 'aws',
    account_id: '',
    region: 'us-east-1',
    role_arn: '',
    client_secret: '',
    domain: ''
  });

  useEffect(() => {
    if (token) {
      fetchData();
      fetchAccounts();
    }
  }, [token]);

  const fetchData = async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      
      // Try to fetch compliance score and findings
      // If there's no data yet, set empty defaults
      try {
        const scoreRes = await axios.get(`${API_BASE}/api/v1/compliance-score`, { headers });
        setScore(scoreRes.data);
      } catch (err) {
        if (err.response?.status !== 401) {
          // No data yet, set default empty score
          setScore({ score: 0, pass: 0, fail: 0, fixed: 0, total: 0, by_severity: {} });
        } else {
          throw err;
        }
      }
      
      try {
        const findingsRes = await axios.get(`${API_BASE}/api/v1/findings?status=FAIL`, { headers });
        setFindings(findingsRes.data || []);
      } catch (err) {
        if (err.response?.status !== 401) {
          // No findings yet
          setFindings([]);
        } else {
          throw err;
        }
      }
      
      setLoading(false);
    } catch (err) {
      console.error(err);
      if (err.response?.status === 401) {
        setToken(null);
        localStorage.removeItem('token');
      }
      setLoading(false);
    }
  };

  const fetchAccounts = async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const res = await axios.get(`${API_BASE}/api/v1/cloud-accounts`, { headers });
      setAccounts(res.data || []);
      if (res.data && res.data.length > 0 && !selectedAccount) {
        setSelectedAccount(res.data[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch accounts:', err);
    }
  };

  const handleAddAccount = async () => {
    try {
      // Check if token exists
      if (!token) {
        setMessage({ type: 'error', text: 'Please login again. Your session may have expired.' });
        return;
      }
      
      const headers = { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
      
      // Build credentials object based on provider
      let credentials = {};
      if (newAccount.provider === 'aws') {
        credentials = { role_arn: newAccount.role_arn };
      } else if (newAccount.provider === 'azure') {
        credentials = {
          subscription_id: newAccount.account_id,
          tenant_id: newAccount.region,
          client_id: newAccount.role_arn,
          client_secret: newAccount.client_secret
        };
      } else if (newAccount.provider === 'm365') {
        credentials = {
          tenant_id: newAccount.account_id,
          client_id: newAccount.region,
          client_secret: newAccount.role_arn,
          domain: newAccount.domain
        };
      }
      
      const accountData = {
        organization_id: 1,
        name: newAccount.name,
        provider: newAccount.provider,
        account_id: newAccount.account_id,
        region: newAccount.region,
        credentials: credentials
      };
      
      console.log('Sending account data:', accountData);
      const response = await axios.post(`${API_BASE}/api/v1/cloud-accounts`, accountData, { headers });
      console.log('Response:', response.data);
      
      setMessage({ type: 'success', text: 'Cloud account added successfully' });
      setShowAddAccount(false);
      setNewAccount({ name: '', provider: 'aws', account_id: '', region: 'us-east-1', role_arn: '', client_secret: '', domain: '' });
      fetchAccounts();
    } catch (err) {
      console.error('Error adding account:', err);
      console.error('Error response:', err.response);
      
      if (err.response?.status === 401) {
        setMessage({ type: 'error', text: 'Authentication failed. Please logout and login again.' });
        // Clear token and force re-login
        localStorage.removeItem('token');
        setToken(null);
      } else {
        const errorMsg = err.response?.data?.detail || 'Failed to add account';
        setMessage({ type: 'error', text: errorMsg });
      }
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const formData = new FormData();
      formData.append('username', loginForm.email);
      formData.append('password', loginForm.password);
      const res = await axios.post(`${API_BASE}/api/v1/auth/login`, formData);
      const newToken = res.data.access_token;
      setToken(newToken);
      localStorage.setItem('token', newToken);
      setMessage({ type: 'success', text: 'Login successful' });
    } catch (err) {
      setMessage({ type: 'error', text: 'Login failed' });
    }
  };

  const handleScan = async () => {
    if (!selectedAccount) {
      setMessage({ type: 'error', text: 'Please add a cloud account first' });
      return;
    }
    setScanLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      await axios.post(`${API_BASE}/api/v1/scans`, { account_id: selectedAccount }, { headers });
      setMessage({ type: 'success', text: 'Scan started successfully' });
      setTimeout(fetchData, 3000);
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Scan failed' });
    } finally {
      setScanLoading(false);
    }
  };

  const handleRemediate = async (findingId) => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      await axios.post(`${API_BASE}/api/v1/remediations`, 
        { finding_id: findingId, dry_run: false }, { headers });
      setMessage({ type: 'success', text: 'Remediation executed' });
      fetchData();
    } catch (err) {
      setMessage({ type: 'error', text: 'Remediation failed' });
    }
  };

  const exportReport = async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      // Send as query parameters instead of body
      const params = { organization_id: 1, format: 'pdf' };
      const res = await axios.post(
        `${API_BASE}/api/v1/audit-reports`,
        null,  // No body needed
        { headers, params }  // Send as query params
      );
      
      if (res.data.download_url) {
        window.open(res.data.download_url, '_blank');
        setMessage({ type: 'success', text: 'Report generated' });
      } else {
        // For local/demo mode without S3, show message
        setMessage({ type: 'info', text: 'Report generated successfully. Download URL not available in demo mode.' });
      }
    } catch (err) {
      console.error('Report error:', err.response?.data);
      const errorMsg = err.response?.data?.detail || 'Report generation failed. Please add cloud accounts and run scans first.';
      setMessage({ type: 'error', text: errorMsg });
    }
  };

  if (!token) {
    return (
      <Container maxWidth="sm" sx={{ mt: 8 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom>Compliance Platform Login</Typography>
          <form onSubmit={handleLogin}>
            <input type="email" placeholder="Email" value={loginForm.email}
              onChange={(e) => setLoginForm({...loginForm, email: e.target.value})}
              style={{ width: '100%', padding: '12px', marginBottom: '12px', fontSize: '16px' }} />
            <input type="password" placeholder="Password" value={loginForm.password}
              onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
              style={{ width: '100%', padding: '12px', marginBottom: '12px', fontSize: '16px' }} />
            <Button type="submit" variant="contained" fullWidth>Login</Button>
          </form>
          {message && <Alert severity={message.type} sx={{ mt: 2 }}>{message.text}</Alert>}
        </Paper>
      </Container>
    );
  }

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;

  const chartData = score ? [
    { name: 'PASS', value: score.pass },
    { name: 'FAIL', value: score.fail },
    { name: 'FIXED', value: score.fixed }
  ] : [];

  const severityData = score?.by_severity ? Object.entries(score.by_severity).map(([name, value]) => ({ name, value })) : [];

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>Autonomous Compliance Platform</Typography>
          <Button color="inherit" onClick={() => setShowAddAccount(true)}>+ Add Cloud Account</Button>
          <Button color="inherit" onClick={exportReport}>Export Report</Button>
          <Button color="inherit" onClick={() => { setToken(null); localStorage.removeItem('token'); }}>Logout</Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4 }}>
        {message && <Alert severity={message.type} onClose={() => setMessage(null)} sx={{ mb: 2 }}>{message.text}</Alert>}
        
        {(!findings || findings.length === 0) && score?.total === 0 && (
          <Alert severity="info" sx={{ mb: 3 }}>
            <strong>Welcome to the Compliance Platform!</strong><br/>
            To get started: Add a cloud account, then run your first compliance scan.
          </Alert>
        )}

        {/* Account Selector */}
        {accounts.length > 0 && (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Select Cloud Account</InputLabel>
                    <Select
                      value={selectedAccount || ''}
                      label="Select Cloud Account"
                      onChange={(e) => setSelectedAccount(e.target.value)}
                    >
                      {accounts.map((acc) => (
                        <MenuItem key={acc.id} value={acc.id}>
                          {acc.name} ({acc.provider} - {acc.account_id})
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Button 
                    variant="contained" 
                    size="large"
                    onClick={handleScan} 
                    disabled={scanLoading || !selectedAccount}
                    fullWidth
                  >
                    {scanLoading ? 'Scanning...' : '🔍 Run Compliance Scan'}
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        )}

        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Compliance Score</Typography>
                <Typography variant="h2" color="primary">{score?.score || 0}%</Typography>
                <Typography variant="body2" color="textSecondary">
                  {score?.pass || 0} passed, {score?.fail || 0} failed, {score?.fixed || 0} fixed
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Total Controls</Typography>
                <Typography variant="h2">{score?.total || 0}</Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                  {accounts.length} cloud account(s) connected
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Critical Findings</Typography>
                <Typography variant="h2" color="error">
                  {findings.filter(f => f.severity === 'critical').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Control Status Distribution</Typography>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie data={chartData} cx="50%" cy="50%" labelLine={false} 
                      label={e => e.name} outerRadius={80} fill="#8884d8" dataKey="value">
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Failures by Severity</Typography>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={severityData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#8884d8">
                      {severityData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={SEVERITY_COLORS[entry.name] || '#999'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Failed Controls (Requires Attention)</Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Control ID</TableCell>
                        <TableCell>Resource</TableCell>
                        <TableCell>Severity</TableCell>
                        <TableCell>Detected</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {findings && findings.length > 0 ? (
                        findings.slice(0, 10).map((finding) => (
                          <TableRow key={finding.id}>
                            <TableCell>{finding.control_id}</TableCell>
                            <TableCell sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {finding.resource_id}
                            </TableCell>
                            <TableCell>
                              <Chip label={finding.severity} size="small" 
                                sx={{ bgcolor: SEVERITY_COLORS[finding.severity], color: 'white' }} />
                            </TableCell>
                            <TableCell>{new Date(finding.detected_at).toLocaleDateString()}</TableCell>
                            <TableCell>
                              {finding.can_remediate && (
                                <Button size="small" variant="outlined" 
                                  onClick={() => handleRemediate(finding.id)}>
                                  Remediate
                                </Button>
                              )}
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                            <Typography color="textSecondary">
                              No failed controls found. Run a scan to see results.
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>

      {/* Add Cloud Account Dialog */}
      <Dialog open={showAddAccount} onClose={() => setShowAddAccount(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Cloud Account</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Account Name"
              value={newAccount.name}
              onChange={(e) => setNewAccount({...newAccount, name: e.target.value})}
              margin="normal"
              placeholder="e.g., Production AWS"
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Provider</InputLabel>
              <Select
                value={newAccount.provider}
                label="Provider"
                onChange={(e) => setNewAccount({...newAccount, provider: e.target.value})}
              >
                <MenuItem value="aws">AWS</MenuItem>
                <MenuItem value="azure">Azure</MenuItem>
                <MenuItem value="m365">Microsoft 365</MenuItem>
              </Select>
            </FormControl>
            {/* AWS-specific fields */}
            {newAccount.provider === 'aws' && (
              <>
                <TextField
                  fullWidth
                  label="AWS Account ID"
                  value={newAccount.account_id}
                  onChange={(e) => setNewAccount({...newAccount, account_id: e.target.value})}
                  margin="normal"
                  placeholder="e.g., 123456789012"
                  helperText="Your 12-digit AWS Account ID"
                />
                <TextField
                  fullWidth
                  label="Region"
                  value={newAccount.region}
                  onChange={(e) => setNewAccount({...newAccount, region: e.target.value})}
                  margin="normal"
                  placeholder="e.g., us-east-1"
                  helperText="AWS region for compliance scanning"
                />
                <TextField
                  fullWidth
                  label="IAM Role ARN"
                  value={newAccount.role_arn}
                  onChange={(e) => setNewAccount({...newAccount, role_arn: e.target.value})}
                  margin="normal"
                  placeholder="arn:aws:iam::123456789012:role/ComplianceReadOnlyRole"
                  helperText="Read-only IAM role for compliance scanning"
                  multiline
                />
              </>
            )}

            {/* Azure-specific fields */}
            {newAccount.provider === 'azure' && (
              <>
                <TextField
                  fullWidth
                  label="Subscription ID"
                  value={newAccount.account_id}
                  onChange={(e) => setNewAccount({...newAccount, account_id: e.target.value})}
                  margin="normal"
                  placeholder="e.g., xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                  helperText="Azure Subscription ID (GUID format)"
                />
                <TextField
                  fullWidth
                  label="Tenant ID"
                  value={newAccount.region}
                  onChange={(e) => setNewAccount({...newAccount, region: e.target.value})}
                  margin="normal"
                  placeholder="e.g., xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                  helperText="Azure Active Directory Tenant ID"
                />
                <TextField
                  fullWidth
                  label="Application (Client) ID"
                  value={newAccount.role_arn}
                  onChange={(e) => setNewAccount({...newAccount, role_arn: e.target.value})}
                  margin="normal"
                  placeholder="e.g., xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                  helperText="Azure AD App Registration Client ID"
                />
                <TextField
                  fullWidth
                  label="Client Secret"
                  value={newAccount.client_secret || ''}
                  onChange={(e) => setNewAccount({...newAccount, client_secret: e.target.value})}
                  margin="normal"
                  type="password"
                  placeholder="Enter client secret value"
                  helperText="Application client secret for authentication"
                />
              </>
            )}

            {/* Microsoft 365-specific fields */}
            {newAccount.provider === 'm365' && (
              <>
                <TextField
                  fullWidth
                  label="Tenant ID"
                  value={newAccount.account_id}
                  onChange={(e) => setNewAccount({...newAccount, account_id: e.target.value})}
                  margin="normal"
                  placeholder="e.g., xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                  helperText="Microsoft 365 Tenant ID"
                />
                <TextField
                  fullWidth
                  label="Application (Client) ID"
                  value={newAccount.region}
                  onChange={(e) => setNewAccount({...newAccount, region: e.target.value})}
                  margin="normal"
                  placeholder="e.g., xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                  helperText="Azure AD App Registration Client ID"
                />
                <TextField
                  fullWidth
                  label="Client Secret"
                  value={newAccount.role_arn}
                  onChange={(e) => setNewAccount({...newAccount, role_arn: e.target.value})}
                  margin="normal"
                  type="password"
                  placeholder="Enter client secret value"
                  helperText="Application client secret for Microsoft Graph API"
                />
                <TextField
                  fullWidth
                  label="Organization Domain"
                  value={newAccount.domain || ''}
                  onChange={(e) => setNewAccount({...newAccount, domain: e.target.value})}
                  margin="normal"
                  placeholder="e.g., contoso.onmicrosoft.com"
                  helperText="Your Microsoft 365 organization domain"
                />
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAddAccount(false)}>Cancel</Button>
          <Button 
            onClick={handleAddAccount} 
            variant="contained"
            disabled={!newAccount.name || !newAccount.account_id}
          >
            Add Account
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default App;

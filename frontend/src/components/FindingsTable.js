import React, { useState } from 'react';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, Button, IconButton, Tooltip, Dialog, DialogTitle,
  DialogContent, DialogActions, Typography, Box
} from '@mui/material';
import { Visibility, Build, Undo } from '@mui/icons-material';
import { SEVERITY_COLORS } from '../types';

const FindingsTable = ({ findings, onRemediate, onRollback }) => {
  const [selectedFinding, setSelectedFinding] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  const handleViewDetails = (finding) => {
    setSelectedFinding(finding);
    setDetailsOpen(true);
  };

  const handleClose = () => {
    setDetailsOpen(false);
    setSelectedFinding(null);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  return (
    <>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
              <TableCell><strong>Control ID</strong></TableCell>
              <TableCell><strong>Resource</strong></TableCell>
              <TableCell><strong>Severity</strong></TableCell>
              <TableCell><strong>Status</strong></TableCell>
              <TableCell><strong>Detected</strong></TableCell>
              <TableCell><strong>Actions</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {findings && findings.length > 0 ? (
              findings.map((finding) => (
                <TableRow key={finding.id} hover>
                  <TableCell>{finding.control_id}</TableCell>
                  <TableCell sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {finding.resource_id}
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={finding.severity} 
                      size="small"
                      sx={{ 
                        bgcolor: SEVERITY_COLORS[finding.severity],
                        color: 'white',
                        fontWeight: 'bold'
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={finding.status}
                      size="small"
                      color={finding.status === 'FAIL' ? 'error' : 'default'}
                    />
                  </TableCell>
                  <TableCell>{formatDate(finding.detected_at)}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Tooltip title="View Details">
                        <IconButton 
                          size="small" 
                          onClick={() => handleViewDetails(finding)}
                          color="primary"
                        >
                          <Visibility fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      
                      {finding.can_remediate && finding.status === 'FAIL' && (
                        <Tooltip title="Remediate">
                          <Button 
                            size="small" 
                            variant="outlined"
                            startIcon={<Build />}
                            onClick={() => onRemediate(finding.id)}
                          >
                            Fix
                          </Button>
                        </Tooltip>
                      )}
                      
                      {finding.status === 'FIXED' && onRollback && (
                        <Tooltip title="Rollback">
                          <IconButton 
                            size="small" 
                            onClick={() => onRollback(finding.id)}
                            color="warning"
                          >
                            <Undo fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography color="text.secondary">No findings to display</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Details Dialog */}
      <Dialog open={detailsOpen} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>Finding Details</DialogTitle>
        <DialogContent>
          {selectedFinding && (
            <Box>
              <Typography variant="subtitle2" color="text.secondary">Control ID</Typography>
              <Typography variant="body1" gutterBottom>{selectedFinding.control_id}</Typography>
              
              <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }}>Resource ID</Typography>
              <Typography variant="body1" gutterBottom sx={{ wordBreak: 'break-all' }}>
                {selectedFinding.resource_id}
              </Typography>
              
              <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }}>Resource Type</Typography>
              <Typography variant="body1" gutterBottom>{selectedFinding.resource_type}</Typography>
              
              <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }}>Finding Details</Typography>
              <Paper sx={{ p: 2, bgcolor: '#f5f5f5', mt: 1 }}>
                <pre style={{ margin: 0, fontSize: '12px', overflow: 'auto' }}>
                  {JSON.stringify(selectedFinding.finding_details, null, 2)}
                </pre>
              </Paper>
              
              <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }}>Detected At</Typography>
              <Typography variant="body1" gutterBottom>{formatDate(selectedFinding.detected_at)}</Typography>
              
              {selectedFinding.resolved_at && (
                <>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }}>Resolved At</Typography>
                  <Typography variant="body1" gutterBottom>{formatDate(selectedFinding.resolved_at)}</Typography>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default FindingsTable;

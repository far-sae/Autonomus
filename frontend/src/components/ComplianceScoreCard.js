import React from 'react';
import { Card, CardContent, Typography, Box, LinearProgress } from '@mui/material';
import { CheckCircle, Error, Build } from '@mui/icons-material';

const ComplianceScoreCard = ({ score }) => {
  if (!score) return null;

  const getScoreColor = (scoreValue) => {
    if (scoreValue >= 90) return '#4caf50';
    if (scoreValue >= 70) return '#ff9800';
    return '#f44336';
  };

  const scoreColor = getScoreColor(score.score);

  return (
    <Card elevation={3}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Compliance Score
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h2" sx={{ color: scoreColor, fontWeight: 'bold' }}>
            {score.score}%
          </Typography>
        </Box>
        
        <LinearProgress 
          variant="determinate" 
          value={score.score} 
          sx={{ 
            height: 10, 
            borderRadius: 5,
            backgroundColor: '#e0e0e0',
            '& .MuiLinearProgress-bar': {
              backgroundColor: scoreColor
            }
          }} 
        />
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <CheckCircle sx={{ color: '#4caf50', fontSize: 20 }} />
            <Typography variant="body2" color="text.secondary">
              {score.pass} passed
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Error sx={{ color: '#f44336', fontSize: 20 }} />
            <Typography variant="body2" color="text.secondary">
              {score.fail} failed
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Build sx={{ color: '#2196f3', fontSize: 20 }} />
            <Typography variant="body2" color="text.secondary">
              {score.fixed} fixed
            </Typography>
          </Box>
        </Box>
        
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
          Total controls evaluated: {score.total}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default ComplianceScoreCard;

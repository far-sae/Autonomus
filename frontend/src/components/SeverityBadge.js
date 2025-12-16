import React from 'react';
import { Chip } from '@mui/material';
import { SEVERITY_COLORS } from '../types';

const SeverityBadge = ({ severity }) => {
  return (
    <Chip
      label={severity.toUpperCase()}
      size="small"
      sx={{
        bgcolor: SEVERITY_COLORS[severity],
        color: 'white',
        fontWeight: 'bold',
        textTransform: 'uppercase'
      }}
    />
  );
};

export default SeverityBadge;

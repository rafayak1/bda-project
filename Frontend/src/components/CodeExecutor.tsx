import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { Button, Typography, Box, Paper } from '@mui/material';
import axiosInstance from '../pages/axiosConfig';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';

const CodeExecutor = ({ code, setCode }: { code: string, setCode: React.Dispatch<React.SetStateAction<string>> }) => {
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [table, setTable] = useState<{ columns: string[], rows: any[] } | null>(null);
  const [image, setImage] = useState<string | null>(null);

  const runCode = async () => {
    try {
      const res = await axiosInstance.post('/run-code', { code }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setOutput(res.data.message || '');
      setTable(res.data.table || null);
      setImage(res.data.image_url || null); // 👈 set the image here
      if (res.data.generated_code) {
        setCode(res.data.generated_code);
      }
      setError('');
    } catch (err: any) {
      setError(err?.response?.data?.message || 'Execution failed');
      setOutput('');
      setTable(null);
      setImage(null); // clear old image if there's an error
    }
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h6" sx={{ color: 'white' }}>💻 Buff Coder</Typography>
      <Editor
  height="200px"
  defaultLanguage="python"
  value={code}
  onChange={(value) => setCode(value || '')}
  theme="vs-dark"
/>
      <Button onClick={runCode} variant="contained" sx={{ mt: 2 }}>
        Run
      </Button>
  
      {/* Output from print() or final expression */}
      {output && (
        <Paper sx={{ mt: 2, p: 2, backgroundColor: '#111', color: 'lime' }}>
          <pre>{output}</pre>
        </Paper>
      )}
  
      {/* Error block */}
      {error && (
        <Paper sx={{ mt: 2, p: 2, backgroundColor: '#330000', color: 'red' }}>
          <pre>{error}</pre>
        </Paper>
      )}
  
      {/* DataFrame table preview */}
      {table && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle1" sx={{ color: 'white', mb: 1 }}>📊 Result Preview</Typography>
          <TableContainer component={Paper} sx={{ backgroundColor: '#121212' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  {table.columns.map((col, idx) => (
                    <TableCell key={idx} sx={{ color: 'white', fontWeight: 'bold' }}>
                      {col}
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {table.rows.map((row, rowIdx) => (
                  <TableRow key={rowIdx}>
                    {table.columns.map((col, colIdx) => (
                      <TableCell key={colIdx} sx={{ color: 'white' }}>
                        {row[col]}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}
  
      {/* Matplotlib image preview */}
      {image && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle1" sx={{ color: 'white', mb: 1 }}>
            📈 Generated Plot
          </Typography>
          <img src={image} alt="Plot" style={{ maxWidth: '100%' }} />
        </Box>
      )}
    </Box>
  );
};

export default CodeExecutor;
import React, { useState, useRef, useEffect } from 'react';
import { Container, Typography, Box, TextField, Button, Paper, IconButton, Tooltip } from '@mui/material';
import { styled } from '@mui/material/styles';
import SendIcon from '@mui/icons-material/Send';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import Navbar from '../components/Navbar';
import  axiosInstance from '../pages/axiosConfig';
import { Database } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { v4 as uuid } from 'uuid';
import { DataGrid } from '@mui/x-data-grid';
import { Dialog, DialogTitle, DialogContent, CircularProgress } from '@mui/material';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import CodeExecutor from '../components/CodeExecutor';
import ReactMarkdown from 'react-markdown';
import { Select, MenuItem, InputLabel, FormControl } from '@mui/material'; // ✅ Add to imports if not already there

// Comment out these Firebase imports
// import { auth } from '../firebase';
// import { useAuthState } from 'react-firebase-hooks/auth';

// Styled components with updated color scheme
const ChatContainer = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  borderRadius: 16,
  boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.5)',
  marginTop: theme.spacing(3),
  background: 'rgba(0, 0, 0, 0.7)',
  backdropFilter: 'blur(10px)',
  border: '1px solid rgba(75, 85, 99, 0.3)',
}));

const MessagesContainer = styled(Box)(({ theme }) => ({
  height: '400px',
  overflowY: 'auto',
  border: '1px solid rgba(75, 85, 99, 0.3)',
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
  borderRadius: 12,
  background: 'rgba(0, 0, 0, 0.5)',
}));

const MessageBubble = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isUser'
})<{ isUser: boolean }>(({ theme, isUser }) => ({
  padding: theme.spacing(1.5, 2.5),
  borderRadius: 18,
  maxWidth: '70%',
  wordWrap: 'break-word',
  marginBottom: theme.spacing(1.5),
  backgroundColor: isUser 
    ? 'linear-gradient(to right, #4f46e5, #9333ea, #ec4899)' 
    : 'rgba(31, 41, 55, 0.8)',
  background: isUser 
    ? 'linear-gradient(to right, #4f46e5, #9333ea, #ec4899)' 
    : 'rgba(31, 41, 55, 0.8)',
  color: '#ffffff',
  alignSelf: isUser ? 'flex-end' : 'flex-start',
  display: 'inline-block',
  boxShadow: '0 2px 5px rgba(0, 0, 0, 0.2)',
}));

const StyledTextField = styled(TextField)(({ theme }) => ({
  '& .MuiOutlinedInput-root': {
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    color: 'white',
    '& fieldset': {
      borderColor: 'rgba(75, 85, 99, 0.5)',
    },
    '&:hover fieldset': {
      borderColor: 'rgba(99, 102, 241, 0.6)',
    },
    '&.Mui-focused fieldset': {
      borderColor: '#6366f1',
    },
  },
  '& .MuiInputLabel-root': {
    color: 'rgba(156, 163, 175, 0.8)',
  },
  '& .MuiInputBase-input::placeholder': {
    color: 'rgba(156, 163, 175, 0.5)',
  },
}));

const GradientButton = styled(Button)(({ theme }) => ({
  background: 'linear-gradient(to right, #4f46e5, #9333ea, #ec4899)',
  color: 'white',
  fontWeight: 'bold',
  '&:hover': {
    background: 'linear-gradient(to right, #4338ca, #7e22ce, #db2777)',
  },
  padding: '10px 20px',
  borderRadius: '8px',
}));

// const UploadButton = styled(Button)(({ theme }) => ({
//   background: 'linear-gradient(to right, #4f46e5, #9333ea)',
//   color: 'white',
//   fontWeight: 'bold',
//   '&:hover': {
//     background: 'linear-gradient(to right, #4338ca, #7e22ce)',
//   },
//   padding: '10px 20px',
//   borderRadius: '8px',
//   marginBottom: theme.spacing(2),
// }));

const ActionButton = styled(Button)(({ theme }) => ({
  background: 'linear-gradient(to right, #4f46e5, #9333ea, #ec4899)',
  color: 'white',
  fontWeight: 'bold',
  padding: '10px 24px',
  borderRadius: '12px',
  minWidth: '180px',
  '&:hover': {
    background: 'linear-gradient(to right, #4338ca, #7e22ce, #db2777)',
  },
}));

const HiddenInput = styled('input')({
  display: 'none',
});

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  isFile?: boolean;
  fileName?: string;
  downloadUrl?: string;
  tableData?: { columns: string[]; rows: (string | number)[][] } | null;
  imageUrl?: string;
}

const Chatx: React.FC = () => {
  // Replace this line
  // const [user] = useAuthState(auth);
  // With this
  const user = null; // Mock user state

  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [hasUploaded, setHasUploaded] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [previewColumns, setPreviewColumns] = useState<any[]>([]);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [code, setCode] = useState("df.head()");
  const [buffCleanDialogOpen, setBuffCleanDialogOpen] = useState(false);
  const [cleanTarget, setCleanTarget] = useState<'all' | 'columns' | null>(null);
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
  const [strategies, setStrategies] = useState<string[]>([]);
  const [availableColumns, setAvailableColumns] = useState<string[]>([]);
  const [submittingBuffClean, setSubmittingBuffClean] = useState(false);
  const [buffVisualizerDialogOpen, setBuffVisualizerDialogOpen] = useState(false);
  const [availableChartColumns, setAvailableChartColumns] = useState<string[]>([]);
  const [availableNumericColumns, setAvailableNumericColumns] = useState<string[]>([]);
  const [chartType, setChartType] = useState("bar");
  const [xAxis, setXAxis] = useState("");
  const [yAxis, setYAxis] = useState("");
  const [submittingBuffVisualizer, setSubmittingBuffVisualizer] = useState(false);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    checkDatasetStatus();
  }, []);

const [isLoading, setIsLoading] = useState(false);
const [awaitingResponse, setAwaitingResponse] = useState(false);
const [isLoggedIn, setIsLoggedIn] = useState(false);

useEffect(() => {
  const token = localStorage.getItem('token');
  setIsLoggedIn(!!token);
}, []);

const checkDatasetStatus = async () => {
  try {
    const response = await axiosInstance.get('/dataset-status', {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
      withCredentials: true,
    });

    const { datasetExists, name } = response.data;
    setHasUploaded(datasetExists);
    const welcomeMessage = datasetExists
      ? `🎉 Welcome back, ${name}! I hope you enjoyed your DataBuff experience last time! BuffBot is locked, loaded, and ready to crunch data for you.\n\nYour previously uploaded dataset is all set. Just type a command like "remove column Age" or "filter rows where Salary > 50000" to get started.\n\nNeed inspiration? Type "commands" to see everything I can do — or just say hi. Let's make your data legendary! 💪📊`
      : `👋 Hey there, ${name}! Welcome to DataBuff! I'm BuffBot, your data-savvy sidekick here at CU Boulder.\n\nBefore we dive into powerful transformations and clever insights, upload a dataset to get the ball rolling.\n\nOnce it's in, you can say things like "show me the columns", "drop missing values", or even ask me to do AI-powered cleaning.\n\nType "commands" anytime to see my powers. Let's turn data into decisions, Buff-style! 🦬⚡`;

    setMessages([
      {
        id: Date.now().toString(),
        text: welcomeMessage,
        isUser: false,
        timestamp: new Date(),
      },
    ]);
  } catch (error) {
    console.error("Error checking dataset status:", error);
  }
};

const handleSendMessage = async () => {
  const token = localStorage.getItem('token');
  if (!token) {
    navigate('/signup');
    return;
  }

  if (!message.trim()) return;

  const newUserMessage: Message = {
    id: Date.now().toString(),
    text: message,
    isUser: true,
    timestamp: new Date(),
  };
  setMessages((prev) => [...prev, newUserMessage]);
  setMessage('');
  setIsLoading(true);

  try {
    const response = await axiosInstance.post(
      '/transform',
      { command: message },
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        withCredentials: true,
      }
    );

    const {
      message: botText,
      download_url,
      followup_message,
      image_url,
      table,
      generated_code
    } = response.data;

    if (generated_code) {
      setCode(generated_code);
    }

    const messagesToAdd: Message[] = [];

    if (botText) {
      messagesToAdd.push({
        id: uuid(),
        text: botText,
        isUser: false,
        timestamp: new Date(),
      });
    }

    if (image_url) {
      messagesToAdd.push({
        id: uuid(),
        text: '',
        isUser: false,
        timestamp: new Date(),
        imageUrl: image_url,
      });
    }

    if (download_url) {
      messagesToAdd.push({
        id: uuid(),
        text: '',
        isUser: false,
        timestamp: new Date(),
        isFile: true,
        fileName: 'Download Transformed Dataset',
        downloadUrl: download_url,
      });
    }

    if (table) {
      messagesToAdd.push({
        id: uuid(),
        text: '',
        isUser: false,
        timestamp: new Date(),
        tableData: table,
      });
    }

    if (followup_message) {
      messagesToAdd.push({
        id: uuid(),
        text: followup_message,
        isUser: false,
        timestamp: new Date(),
      });
    }

    setMessages((prev) => [...prev, ...messagesToAdd]);
  } catch (err: any) {
    const errorMessage: Message = {
      id: Date.now().toString(),
      text: err.response?.data?.message || 'Something went wrong.',
      isUser: false,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, errorMessage]);
  } finally {
    setIsLoading(false);
  }
};

const handlePreviewDataset = async () => {
  setLoadingPreview(true);
  setPreviewOpen(true);
  try {
    const response = await axiosInstance.get('/preview', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    });

    const { data } = response;
    if (data.rows && data.columns) {
      setPreviewData(data.rows);
      setPreviewColumns(
        data.columns.map((col: string) => ({
          field: col,
          headerName: col,
          width: 150,
        }))
      );
    }
  } catch (error) {
    console.error('Failed to fetch preview:', error);
  } finally {
    setLoadingPreview(false);
  }
};

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const token = localStorage.getItem('token');
  if (!token) {
    navigate('/signup');
    return;
  }
    const files = event.target.files;
    if (files && files.length > 0) {
      const file = files[0]; // only support 1 file at a time
      setUploadedFiles((prev) => [...prev, file]);
  
      const fileMessage: Message = {
        id: Date.now().toString(),
        text: `Uploaded: ${file.name}`,
        isUser: true,
        timestamp: new Date(),
        isFile: true,
        fileName: file.name,
      };
  
      const formData = new FormData();
      formData.append('file', file);
      try {
        const response = await axiosInstance.post('/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          withCredentials: true,
        });
      
        setMessages((prev) => [...prev, fileMessage]);
      
        setHasUploaded(true);
      
        setTimeout(() => {
          const botMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: `I've received your document. What would you like to know about it?`,
            isUser: false,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, botMessage]);
        }, 3000);
      } catch (error: any) {
        console.error(error.response?.data?.message || 'Upload failed');
      }
      setHasUploaded(true);
  
      // allow re-upload of same file
      event.target.value = '';
    }
  };

  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };
    
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      localStorage.removeItem('token');
      navigate('/login'); // Redirect to login page after logout
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handleBuffCleanClick = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return navigate('/login');
  
      const response = await axiosInstance.post(
        '/buff-clean',
        {}, // You can later add column/strategy config here
        {
          headers: { Authorization: `Bearer ${token}` },
          withCredentials: true,
        }
      );
  
      const {
        transformation_summary,
        download_url,
        followup_message
      } = response.data;
      console.log("Buff Clean response:", response.data);
  
      const cleanMessages: Message[] = [
        {
          id: uuid(),
          text: transformation_summary,
          isUser: false,
          timestamp: new Date(),
        },
        {
          id: uuid(),
          text: '',
          isUser: false,
          timestamp: new Date(),
          isFile: true,
          fileName: 'Cleaned Dataset',
          downloadUrl: download_url,
        },
        {
          id: uuid(),
          text: followup_message,
          isUser: false,
          timestamp: new Date(),
        },
      ];
  
      setMessages((prev) => [...prev, ...cleanMessages]);
    } catch (err: any) {
      console.error("BuffClean failed:", err);
      const errorMsg: Message = {
        id: uuid(),
        text: err.response?.data?.message || 'Buff Clean failed.',
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    }
  };

  
  const handleBuffVisualizerClick = async () => {
    try {
      const res = await axiosInstance.get('/buff-visualizer-options', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
  
      const columns = res.data.columns || [];
      const numeric = res.data.numeric || [];
  
      setAvailableChartColumns(columns);
      setAvailableNumericColumns(numeric);
      setXAxis(columns[0] || "");
      setYAxis(numeric[0] || "");
  
      setBuffVisualizerDialogOpen(true);
    } catch (err) {
      console.error('Failed to fetch Buff Visualizer options:', err);
    }
  };
  
  const handleBuffTrainerClick = async () => {
    // Placeholder: we'll define backend logic next
    alert("🤖 Buff Trainer clicked! Logic coming next...");
  };

  return (
    // 1) Top-level Box to ensure the entire background is black:
    <Box 
      sx={{ 
        backgroundColor: 'black', 
        color: 'white', 
        minHeight: '100vh', 
        width: '100%',
      }}
    >
      {/* Navigation */}
      <motion.nav 
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ type: "spring", stiffness: 100 }}
        className="bg-black border-b border-gray-800 fixed w-full top-0 z-50"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <Link to="/" style={{ textDecoration: 'none' }}>
              <motion.div 
                whileHover={{ scale: 1.05 }}
                className="flex items-center"
              >
                <Database className="h-8 w-8 text-white" />
                <span className="ml-2 text-xl font-bold text-white">DataBuff</span>
              </motion.div>
            </Link>
  
            <div className="flex items-center space-x-8">
              {isLoggedIn && (
                <motion.button 
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleLogout}
                  className="border border-indigo-600 text-indigo-600 px-4 py-2 rounded-md hover:bg-indigo-50 transition-colors duration-200"
                >
                  <span className="font-medium text-white hover:text-zinc-300 transition-colors">
                    Logout
                  </span>
                </motion.button>
              )}
            </div>
          </div>
        </div>
      </motion.nav>
  
      {/* 2) Flex container for sidebar & main content */}
      <Box sx={{ display: 'flex', pt: 0 }}>
        {/* Left Vertical Button Bar */}
        <Box
          sx={{
            width: 80,
            height: '100vh',
            backgroundColor: '#111827',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            paddingTop: 10,
            gap: 2,
            position: 'fixed',
            top: 64, // below the navbar height
            left: 0,
            zIndex: 10,
            borderRight: '1px solid #1f2937',
          }}
        >
<Tooltip title="Buff Clean 🧼" placement="right">
  <Button
    sx={{
      minWidth: 0,
      width: 56,
      height: 56,
      borderRadius: '50%',
      background: 'linear-gradient(to right, #4f46e5, #9333ea)',
      color: 'white',
      fontSize: 24,
      '&:hover': {
        background: 'linear-gradient(to right, #4338ca, #7e22ce)',
      },
    }}
    onClick={async () => {
      try {
        const res = await axiosInstance.get('/buff-clean-options', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        setAvailableColumns(res.data.columns);
        setBuffCleanDialogOpen(true);
      } catch (err) {
        console.error('Failed to fetch Buff Clean options:', err);
      }
    }}
  >
    🧼
  </Button>
</Tooltip>
  
<Tooltip title="Buff Visualizer 📊" placement="right">
  <Button
    sx={{
      minWidth: 0,
      width: 56,
      height: 56,
      borderRadius: '50%',
      background: 'linear-gradient(to right, #4f46e5, #9333ea)',
      color: 'white',
      fontSize: 24,
      '&:hover': {
        background: 'linear-gradient(to right, #4338ca, #7e22ce)',
      },
    }}
    onClick={async () => {
      try {
        const res = await axiosInstance.get('/buff-visualizer-options', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
    
        const columns = res.data.all_columns || [];
        const numeric = res.data.numeric_columns || [];
    
        setAvailableChartColumns(columns);
        setAvailableNumericColumns(numeric);
        setXAxis(columns[0] || "");
        setYAxis(columns[1] || "");
        setChartType("bar");
        setBuffVisualizerDialogOpen(true);
      } catch (err) {
        console.error('Failed to fetch Buff Visualizer options:', err);
      }
    }}
  >
    📊
  </Button>
</Tooltip>
  
          <Tooltip title="Buff Trainer 🤖" placement="right">
            <Button
              sx={{
                minWidth: 0,
                width: 56,
                height: 56,
                borderRadius: '50%',
                background: 'linear-gradient(to right, #4f46e5, #9333ea)',
                color: 'white',
                fontSize: 24,
                '&:hover': {
                  background: 'linear-gradient(to right, #4338ca, #7e22ce)',
                },
              }}
              onClick={handleBuffTrainerClick}
            >
              🤖
            </Button>
          </Tooltip>
        </Box>
  
        {/* 3) Main Content – shifted to the right so the sidebar doesn't overlap */}
        <Box sx={{ flexGrow: 1, ml: '80px' }}>
          {/* 4) Use a Container if you still want a narrower center column. 
              If you want it to fill the whole screen, remove maxWidth or set maxWidth={false}. */}
          <Container maxWidth="md" sx={{ pt: 12, pb: 4 }}>
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Typography 
                variant="h2" 
                component="h1" 
                gutterBottom
                sx={{ 
                  fontWeight: 'bold',
                  background: 'linear-gradient(to right, #ffffff, #a5b4fc, #8b5cf6)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  mb: 2
                }}
              >
                DataBuff
              </Typography>
              <Typography 
                variant="h6" 
                sx={{ color: 'rgba(156, 163, 175, 0.9)', mb: 4 }}
              >
                Speak, Modify, Achieve: Your Dataset, Refined by Intelligent Conversation.
              </Typography>
            </Box>
            
            <ChatContainer>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography 
                  variant="h5" 
                  component="h2" 
                  sx={{ 
                    fontWeight: 'bold',
                    background: 'linear-gradient(to right, #ffffff, #a5b4fc)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                  }}
                >
                  Chat with Our Assistant
                </Typography>
                
                <Box>
                  <HiddenInput
                    ref={fileInputRef}
                    accept=".pdf,.doc,.docx,.txt,.csv,.xlsx"
                    id="file-upload"
                    type="file"
                    onChange={handleFileUpload}
                    multiple
                  />
                  <Tooltip title="Upload Documents">
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <ActionButton
                        startIcon={<UploadFileIcon />}
                        onClick={triggerFileUpload}
                      >
                        {hasUploaded ? 'Replace Dataset' : 'Upload Dataset'}
                      </ActionButton>
  
                      {hasUploaded && (
                        <ActionButton onClick={handlePreviewDataset}>
                          View Dataset
                        </ActionButton>
                      )}
                    </Box>
                  </Tooltip>
                </Box>
              </Box>
  
              <MessagesContainer sx={{ display: 'flex', flexDirection: 'column' }}>
                {messages.map((msg) => (
                  <Box
                    key={msg.id}
                    sx={{ display: 'flex', justifyContent: msg.isUser ? 'flex-end' : 'flex-start' }}
                  >
                    <MessageBubble isUser={msg.isUser}>
                      {msg.downloadUrl ? (
                        <Button
                          variant="outlined"
                          href={msg.downloadUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          sx={{
                            color: '#fff',
                            borderColor: '#9333ea',
                            '&:hover': {
                              borderColor: '#ec4899',
                              background: 'rgba(255, 255, 255, 0.1)',
                            },
                          }}
                        >
                          Download Transformed Dataset
                        </Button>
                      ) : msg.imageUrl ? (
                        <img 
                          src={msg.imageUrl} 
                          alt="Generated Visualization" 
                          style={{ maxWidth: '100%' }} 
                        />
                      ) : msg.tableData ? (
                        <Box sx={{ mt: 1 }}>
                          <TableContainer component={Paper} sx={{ backgroundColor: '#121212' }}>
                            <Table size="small">
                              <TableHead>
                                <TableRow>
                                  {msg.tableData.columns.map((col, idx) => (
                                    <TableCell key={idx} sx={{ color: 'white', fontWeight: 'bold' }}>
                                      {col}
                                    </TableCell>
                                  ))}
                                </TableRow>
                              </TableHead>
                              <TableBody>
                                {msg.tableData.rows.map((row, rowIdx) => (
                                  <TableRow key={rowIdx}>
                                    {Object.values(row).map((cell, colIdx) => (
                                      <TableCell key={colIdx} sx={{ color: 'white' }}>
                                        {cell}
                                      </TableCell>
                                    ))}
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </TableContainer>
                        </Box>
                      ) : (
                        <ReactMarkdown>{msg.text}</ReactMarkdown>
                      )}
                    </MessageBubble>
                  </Box>
                ))}
                <div ref={messagesEndRef} />
              </MessagesContainer>
  
              <Box sx={{ display: 'flex', gap: 1 }}>
                <StyledTextField
                  fullWidth
                  variant="outlined"
                  placeholder="Type your message here..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleSendMessage();
                    }
                  }}
                  InputProps={{
                    sx: { borderRadius: 2 }
                  }}
                />
                {isLoading ? (
                  <GradientButton disabled variant="contained">
                    Loading...
                  </GradientButton>
                ) : (
                  <GradientButton
                    variant="contained"
                    endIcon={<SendIcon />}
                    onClick={handleSendMessage}
                  >
                    Send
                  </GradientButton>
                )}
              </Box>
            </ChatContainer>
  
            <Box sx={{ mt: 4 }}>
              <CodeExecutor code={code} setCode={setCode} />
            </Box>
          </Container>
        </Box>
      </Box>
  
      {/* Dialogs */}
      <Dialog
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 'bold', color: '#111827' }}>
          Dataset Preview
        </DialogTitle>
        <DialogContent>
          {loadingPreview ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : (
            <div style={{ height: 500, width: '100%', backgroundColor: 'white', borderRadius: 8, padding: 10 }}>
              <DataGrid
                rows={previewData}
                columns={previewColumns}
                pageSize={10}
                getRowId={(row) => row.EVENT_ID || row.id}
                rowsPerPageOptions={[10]}
                disableSelectionOnClick
              />
            </div>
          )}
        </DialogContent>
      </Dialog>
  
      <Dialog open={buffCleanDialogOpen} onClose={() => setBuffCleanDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Buff Clean 🧼</DialogTitle>
        <DialogContent>
          {cleanTarget === null && (
            <Box display="flex" gap={2} mt={2}>
              <Button fullWidth variant="contained" onClick={() => setCleanTarget('all')}>
                Clean Whole Dataset
              </Button>
              <Button fullWidth variant="outlined" onClick={() => setCleanTarget('columns')}>
                Choose Columns
              </Button>
            </Box>
          )}
  
          {cleanTarget && (
            <>
              {cleanTarget === 'columns' && (
                <Box mt={3}>
                  <Typography>Select Columns to Clean:</Typography>
                  <FormControl fullWidth sx={{ mt: 2 }}>
                    <InputLabel id="column-select-label">Select Columns</InputLabel>
                    <Select
                      labelId="column-select-label"
                      multiple
                      value={selectedColumns}
                      onChange={(e) => setSelectedColumns(e.target.value as string[])}
                      renderValue={(selected) => selected.join(', ')}
                    >
                      {availableColumns.map((col) => (
                        <MenuItem key={col} value={col}>
                          {col}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>
              )}
  
              <Box mt={3}>
                <Typography>Choose Cleaning Strategies:</Typography>
                {[
                  { value: 'drop_na_rows', label: 'Drop rows with missing values' },
                  { value: 'fill_missing_with_mean', label: 'Fill missing values with mean' },
                  { value: 'fill_missing_with_median', label: 'Fill missing values with median' },
                  { value: 'fill_missing_with_mode', label: 'Fill missing values with mode' },
                  { value: 'label_encode', label: 'Label encode categorical columns' },
                  { value: 'one_hot_encode', label: 'One-hot encode categorical columns' },
                ].map((opt) => (
                  <Box key={opt.value}>
                    <label>
                      <input
                        type="checkbox"
                        value={opt.value}
                        checked={strategies.includes(opt.value)}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          setStrategies((prev) =>
                            checked ? [...prev, opt.value] : prev.filter((s) => s !== opt.value)
                          );
                        }}
                      />
                      {' ' + opt.label}
                    </label>
                  </Box>
                ))}
              </Box>
  
              <Box mt={3}>
                <Button
                  variant="contained"
                  disabled={submittingBuffClean}
                  onClick={async () => {
                    setSubmittingBuffClean(true);
                    try {
                      const res = await axiosInstance.post('/buff-clean', {
                        columns: cleanTarget === 'columns' ? selectedColumns : null,
                        strategies,
                      }, {
                        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
                      });
  
                      const { transformation_summary, download_url, followup_message } = res.data;
                      const cleanMessages = [
                        {
                          id: uuid(),
                          text: transformation_summary,
                          isUser: false,
                          timestamp: new Date(),
                        },
                        {
                          id: uuid(),
                          text: '',
                          isUser: false,
                          timestamp: new Date(),
                          isFile: true,
                          fileName: 'Download Transformed Dataset',
                          downloadUrl: download_url,
                        },
                        {
                          id: uuid(),
                          text: followup_message,
                          isUser: false,
                          timestamp: new Date(),
                        },
                      ];
                      setMessages((prev) => [...prev, ...cleanMessages]);
                    } catch (err) {
                      console.error('Buff Clean failed:', err);
                    } finally {
                      setSubmittingBuffClean(false);
                      setBuffCleanDialogOpen(false);
                      setCleanTarget(null);
                      setStrategies([]);
                      setSelectedColumns([]);
                    }
                  }}
                >
                  Apply Buff Clean
                </Button>
              </Box>
            </>
          )}
        </DialogContent>
      </Dialog>
      <Dialog open={buffVisualizerDialogOpen} onClose={() => setBuffVisualizerDialogOpen(false)} maxWidth="sm" fullWidth>
  <DialogTitle>Buff Visualizer 📊</DialogTitle>
  <DialogContent>
    <Box mt={2}>
      <FormControl fullWidth>
        <InputLabel id="chart-type-label">Chart Type</InputLabel>
        <Select
          labelId="chart-type-label"
          value={chartType}
          onChange={(e) => setChartType(e.target.value)}
        >
          <MenuItem value="bar">Bar Chart</MenuItem>
          <MenuItem value="line">Line Chart</MenuItem>
          <MenuItem value="scatter">Scatter Plot</MenuItem>
          <MenuItem value="hist">Histogram</MenuItem>
        </Select>
      </FormControl>
    </Box>

    <Box mt={3}>
      <FormControl fullWidth>
        <InputLabel id="x-axis-label">X-Axis Column</InputLabel>
        <Select
          labelId="x-axis-label"
          value={xAxis}
          onChange={(e) => setXAxis(e.target.value)}
        >
          {availableChartColumns.map((col) => (
            <MenuItem key={col} value={col}>{col}</MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>

    {chartType !== "hist" && (
      <Box mt={3}>
        <FormControl fullWidth>
          <InputLabel id="y-axis-label">Y-Axis Column</InputLabel>
          <Select
            labelId="y-axis-label"
            value={yAxis}
            onChange={(e) => setYAxis(e.target.value)}
          >
            {availableNumericColumns.map((col) => (
              <MenuItem key={col} value={col}>{col}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>
    )}

    <Box mt={4}>
    <Button
  fullWidth
  variant="contained"
  disabled={submittingBuffVisualizer}
  onClick={async () => {
    setSubmittingBuffVisualizer(true);
    try {
      const payload: any = {
        chart_type: chartType,
  x: xAxis,
  y: chartType === "hist" ? null : yAxis,
      };

      const res = await axiosInstance.post('/buff-visualizer', payload, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });

      const { image_url, description } = res.data;

      const messagesToAdd = [
        {
          id: uuid(),
          text: description || "Here’s your chart! 📊",
          isUser: false,
          timestamp: new Date(),
        },
        {
          id: uuid(),
          text: '',
          isUser: false,
          timestamp: new Date(),
          imageUrl: image_url,
        }
      ];
      setMessages((prev) => [...prev, ...messagesToAdd]);
    } catch (err) {
      console.error("Buff Visualizer failed:", err);
    } finally {
      setSubmittingBuffVisualizer(false);
      setBuffVisualizerDialogOpen(false);
    }
  }}
>
  Generate Chart
</Button>
    </Box>
  </DialogContent>
</Dialog>
    </Box>
  );
  };
    
  export default Chatx;
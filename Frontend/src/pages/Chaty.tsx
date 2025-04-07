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

const UploadButton = styled(Button)(({ theme }) => ({
  background: 'linear-gradient(to right, #4f46e5, #9333ea)',
  color: 'white',
  fontWeight: 'bold',
  '&:hover': {
    background: 'linear-gradient(to right, #4338ca, #7e22ce)',
  },
  padding: '10px 20px',
  borderRadius: '8px',
  marginBottom: theme.spacing(2),
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
}

const Chatx: React.FC = () => {
  // Replace this line
  // const [user] = useAuthState(auth);
  // With this
  const user = null; // Mock user state

  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: `Hello! How can I help you today? You can upload documents for analysis.

      Welcome to Intelligent Service! Upload your dataset and perform transformations effortlessly.
      
      Supported Commands:
      ● remove column <column_name>
        Example: remove column Age
      ● rename column <old_name> to <new_name>
        Example: rename column Age to Years
      ● filter rows where <condition>
        Example: filter rows where Age > 25
      ● columns
        Example: columns (to list all column names)
      ● size
        Example: size (to get the dataset dimensions),
      ● commands
        Example: commands (to get all the available commands)`,
      isUser: false,
      timestamp: new Date(),
    },
  ]);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [hasUploaded, setHasUploaded] = useState(false);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

const [isLoading, setIsLoading] = useState(false);
const [awaitingResponse, setAwaitingResponse] = useState(false);

const handleSendMessage = async () => {
  if (!message.trim()) return;

  const inputText = message;
  setMessage('');
  setIsLoading(true);

  const newUserMessage: Message = {
    id: uuid(),
    text: inputText,
    isUser: true,
    timestamp: new Date(),
  };
  setMessages((prev) => [...prev, newUserMessage]);

  const tryTransform = async (retry = 0) => {
    try {
      const response = await axiosInstance.post(
        '/transform',
        { command: inputText },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
          withCredentials: true,
        }
      );

      const { message: botText, download_url, followup_message } = response.data;

      const responseMessages: Message[] = [];

      responseMessages.push({
        id: uuid(),
        text: botText,
        isUser: false,
        timestamp: new Date(),
        ...(download_url && { downloadUrl: download_url }),
      });

      if (download_url) {
        responseMessages.push({
          id: uuid(),
          text: '',
          isUser: false,
          timestamp: new Date(),
          isFile: true,
          fileName: download_url, // actual URL goes here
        });
      }

      if (followup_message) {
        responseMessages.push({
          id: uuid(),
          text: followup_message,
          isUser: false,
          timestamp: new Date(),
        });
        setAwaitingResponse(true);
      }

      setMessages((prev) => [...prev, ...responseMessages]);
    } catch (err: any) {
      if (retry < 2) {
        await tryTransform(retry + 1); // try again
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: uuid(),
            text: err?.response?.data?.message || 'Something went wrong. Please try again later.',
            isUser: false,
            timestamp: new Date(),
          },
        ]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (awaitingResponse && (inputText.toLowerCase() === 'yes' || inputText.toLowerCase() === 'no')) {
    setAwaitingResponse(false);
  }

  await tryTransform();
};

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
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
     
      
    //   // Simulate bot response to file upload
    //   setTimeout(() => {
    //     const botMessage: Message = {
    //       id: (Date.now() + 1).toString(),
    //       text: `I've received your document${newFiles.length > 1 ? 's' : ''}. What would you like to know about ${newFiles.length > 1 ? 'them' : 'it'}?`,
    //       isUser: false,
    //       timestamp: new Date(),
    //     };
    //     setMessages((prev) => [...prev, botMessage]);
    //   }, 4000);
    // }
    
  //   // Clear the input value so the same file can be uploaded again
  //   if (event.target) {
  //     event.target.value = '';
  //   }
  // };

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

  return (
    

<div>
<div className="">
      {/* Navigation */}
      <motion.nav 
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ type: "spring", stiffness: 100 }}
        className="bg-black border-b border-gray-800 fixed w-full top-0 z-50"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <motion.div 
              whileHover={{ scale: 1.05 }}
              className="flex items-center"
            >
              <Database className="h-8 w-8 text-white" />
              <span className="ml-2 text-xl font-bold text-white">DataTransform AI</span>
            </motion.div>
            <div className="flex items-center space-x-8">
              
             
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
            </div>
          </div>
        </div>
      </motion.nav>

     
    </div>






    <div className="min-h-screen bg-black text-white">
   
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
            DataTransform AI
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
              <UploadButton
                variant="contained"
                startIcon={<UploadFileIcon />}
                onClick={triggerFileUpload}
              >
                {hasUploaded ? 'Replace Dataset' : 'Upload Dataset'}
            </UploadButton>
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
    ) : (
      msg.text.split('\n').map((line, index) => (
        <p key={index}>{line}</p>
      ))
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
      </Container>
    </div>
    </div>
  );
};

export default Chatx; 
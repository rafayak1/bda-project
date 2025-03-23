import React, { useState, useRef, useEffect } from 'react';
import { Container, Typography, Box, TextField, Button, Paper, IconButton, Tooltip } from '@mui/material';
import { styled } from '@mui/material/styles';
import SendIcon from '@mui/icons-material/Send';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import Navbar from '../components/Navbar';
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
      text: 'Hello! How can I help you today? You can upload documents for analysis.',
      isUser: false,
      timestamp: new Date(),
    },
  ]);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = () => {
    if (message.trim()) {
      // Add user message
      const newUserMessage: Message = {
        id: Date.now().toString(),
        text: message,
        isUser: true,
        timestamp: new Date(),
      };
      
      setMessages((prev) => [...prev, newUserMessage]);
      setMessage('');
      setTimeout(() => {
      // Simulate bot response
      if (message.trim()=="size") {
        // Add user message
        const botMessage: Message  = {
          id: Date.now().toString(),
          text: "Dataset Dimensions:Rows: 6944800, Columns: 7",
          isUser: false,
          timestamp: new Date(),
        };
        
        setMessages((prev) => [...prev, botMessage]);
        setMessage('');
      }}, 2000);
      setTimeout(() => {
      if (message.trim()=="columns") {
        // Add user message
        const botMessage: Message  = {
          id: Date.now().toString(),
          text: "Dataset Columns: Timestamp, Open, High, Low, Close, Volume,datetime",
          isUser: false,
          timestamp: new Date(),
        };
        
        setMessages((prev) => [...prev, botMessage]);
        setMessage('');
      }}, 2000);
      setTimeout(() => {
      if (message.trim()=="Remove column open") {
       
        const botMessage: Message  = {
          id: Date.now().toString(),
          text: `Download your transformed dataset here: "`,
          isUser: false,
          timestamp: new Date(),
        };
        
        setMessages((prev) => [...prev, botMessage]);
        setMessage('');
      } }, 4000);
      
      setTimeout(() => {
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: "Anything else you would like to know about",
          isUser: false,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, botMessage]);
      }, 4500);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const newFiles = Array.from(files);
      setUploadedFiles((prev) => [...prev, ...newFiles]);
      
      // Add file upload message
      const fileMessage: Message = {
        id: Date.now().toString(),
        text: `Uploaded: ${newFiles.map(f => f.name).join(', ')}`,
        isUser: true,
        timestamp: new Date(),
        isFile: true,
        fileName: newFiles.map(f => f.name).join(', ')
      };
      
      setMessages((prev) => [...prev, fileMessage]);
      
      // Simulate bot response to file upload
      setTimeout(() => {
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: `I've received your document${newFiles.length > 1 ? 's' : ''}. What would you like to know about ${newFiles.length > 1 ? 'them' : 'it'}?`,
          isUser: false,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, botMessage]);
      }, 4000);
    }
    
    // Clear the input value so the same file can be uploaded again
    if (event.target) {
      event.target.value = '';
    }
  };

  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };

  return (
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
                  Upload Documents
                </UploadButton>
              </Tooltip>
            </Box>
          </Box>
          
          <MessagesContainer sx={{ display: 'flex', flexDirection: 'column' }}>
            {messages.map((msg) => (
              <Box key={msg.id} sx={{ display: 'flex', justifyContent: msg.isUser ? 'flex-end' : 'flex-start' }}>
                <MessageBubble isUser={msg.isUser}>
                  {msg.isFile ? (
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <AttachFileIcon sx={{ mr: 1 }} />
                      {/* <p dangerouslySetInnerHTML={{ __html: msg.text }} /> */}
                      {msg.text}
                    </Box>
                  ) : (
                    msg.text
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
            <GradientButton 
              variant="contained" 
              endIcon={<SendIcon />}
              onClick={handleSendMessage}
            >
              Send
            </GradientButton>
          </Box>
        </ChatContainer>
      </Container>
    </div>
  );
};

export default Chatx; 
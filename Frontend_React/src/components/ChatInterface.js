import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Container,
  Avatar,
  CircularProgress,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MenuIcon from '@mui/icons-material/Menu';
import SmartToyIcon from '@mui/icons-material/SmartToy'; // AI avatar
import PersonIcon from '@mui/icons-material/Person'; // User avatar
import ReactMarkdown from 'react-markdown'; // <-- Import ReactMarkdown

const ChatInterface = ({ messages = [], onSendMessage, isSidebarOpen, onToggleSidebar }) => {
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const containerRef = useRef(null);
  
  // Function to scroll to bottom when needed
  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom(); // Auto-scroll when messages update
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      setIsTyping(true);
      onSendMessage(input);
      setInput('');
      setTimeout(() => setIsTyping(false), 1000);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Custom components for ReactMarkdown
  const markdownComponents = {
    p: ({node, ...props}) => (
      <Typography variant="body1" component="p" sx={{ mb: 1, color: '#ECECF1' }} {...props} />
    ),
    h1: ({node, ...props}) => (
      <Typography variant="h4" component="h1" sx={{ mt: 2, mb: 1, color: '#ECECF1' }} {...props} />
    ),
    h2: ({node, ...props}) => (
      <Typography variant="h5" component="h2" sx={{ mt: 2, mb: 1, color: '#ECECF1' }} {...props} />
    ),
    h3: ({node, ...props}) => (
      <Typography variant="h6" component="h3" sx={{ mt: 2, mb: 1, color: '#ECECF1' }} {...props} />
    ),
    ul: ({node, ...props}) => (
      <Box component="ul" sx={{ pl: 4, mb: 2, color: '#ECECF1' }} {...props} />
    ),
    ol: ({node, ...props}) => (
      <Box component="ol" sx={{ pl: 4, mb: 2, color: '#ECECF1' }} {...props} />
    ),
    li: ({node, ...props}) => (
      <Box component="li" sx={{ mb: 0.5, color: '#ECECF1' }} {...props} />
    ),
    code: ({node, inline, ...props}) => (
      inline ? 
        <Box component="code" sx={{ 
          backgroundColor: 'rgba(0,0,0,0.2)', 
          p: 0.5, 
          borderRadius: 0.5,
          fontFamily: 'monospace',
          color: '#E0E0E0'
        }} {...props} /> :
        <Box component="pre" sx={{ 
          backgroundColor: 'rgba(0,0,0,0.2)', 
          p: 1.5, 
          borderRadius: 1,
          overflow: 'auto',
          fontFamily: 'monospace',
          color: '#E0E0E0',
          my: 1.5
        }}>
          <Box component="code" sx={{ fontFamily: 'monospace' }} {...props} />
        </Box>
    ),
    blockquote: ({node, ...props}) => (
      <Box component="blockquote" sx={{ 
        borderLeft: '4px solid #10a37f',
        pl: 2,
        py: 0.5,
        my: 1.5,
        color: '#ECECF1',
        backgroundColor: 'rgba(16, 163, 127, 0.1)',
      }} {...props} />
    ),
    a: ({node, ...props}) => (
      <Box 
        component="a" 
        sx={{ 
          color: '#10a37f',
          textDecoration: 'underline',
          '&:hover': {
            color: '#0D8C6D'
          }
        }} 
        {...props} 
      />
    ),
  };

  return (
    <Box component="main" sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#343541', position: 'relative' }}>
      {/* Add this new Box for the menu button */}
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
        <IconButton
          onClick={onToggleSidebar}
          sx={{ 
            color: 'white',
            '&:hover': { backgroundColor: 'rgba(255,255,255,0.1)' }
          }}
        >
          <MenuIcon />
        </IconButton>
      </Box>

      <Container
        maxWidth="md"
        ref={containerRef} // Ref to enable scrolling
        sx={{
          flexGrow: 1,
          overflowY: 'auto',
          py: 3,
          px: { xs: 2, sm: 3 },

          /* Hide Scrollbar */
          scrollbarWidth: 'none', // Firefox
          '&::-webkit-scrollbar': { display: 'none' }, // Chrome, Safari, Edge
        }}
      >
        {messages.map((message, index) => (
          <Box
            key={index}
            sx={{
              display: 'flex',
              mb: 3,
              gap: 2,
              backgroundColor: message.role === 'assistant' ? '#444654' : 'transparent',
              p: { xs: 2, sm: 3 },
              borderRadius: 1,
              width: '100%',
            }}
          >
            <Avatar
              sx={{
                bgcolor: message.role === 'assistant' ? '#10a37f' : '#5436DA',
                width: 36,
                height: 36,
              }}
            >
              {message.role === 'assistant' ? <SmartToyIcon /> : <PersonIcon />}
            </Avatar>
            <Box sx={{ flexGrow: 1 }}>
              {message.role === 'assistant' ? (
                <ReactMarkdown components={markdownComponents}>
                  {message.content}
                </ReactMarkdown>
              ) : (
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', color: '#ECECF1' }}>
                  {message.content}
                </Typography>
              )}
            </Box>
          </Box>
        ))}
        {isTyping && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, backgroundColor: '#444654', borderRadius: 1 }}>
            <Avatar sx={{ bgcolor: '#10a37f' }}>
              <SmartToyIcon />
            </Avatar>
            <CircularProgress size={20} sx={{ color: '#10a37f' }} />
          </Box>
        )}
        <div ref={messagesEndRef} /> {/* For auto-scrolling */}
      </Container>

      <Paper
        component="form"
        onSubmit={handleSubmit}
        sx={{
          p: 2,
          backgroundColor: '#343541',
          borderTop: '1px solid rgba(255,255,255,0.1)',
          boxShadow: '0 0 15px rgba(0,0,0,0.2)',
        }}
      >
        <Container maxWidth="md">
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Send a message..."
              variant="outlined"
              size="small"
              sx={{
                '& .MuiOutlinedInput-root': {
                  backgroundColor: '#40414F',
                  color: 'white',
                  '& fieldset': { borderColor: 'rgba(255,255,255,0.1)' },
                  '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.2)' },
                  '&.Mui-focused fieldset': { borderColor: '#10a37f' },
                },
                '& .MuiOutlinedInput-input::placeholder': { color: 'rgba(255,255,255,0.5)' },
              }}
            />
            <IconButton
              type="submit"
              disabled={!input.trim()}
              sx={{
                alignSelf: 'flex-end',
                color: input.trim() ? '#10a37f' : 'rgba(255,255,255,0.3)',
                mb: 0.5,
                '&:hover': { backgroundColor: 'rgba(16, 163, 127, 0.1)' },
              }}
            >
              <SendIcon />
            </IconButton>
          </Box>
        </Container>
      </Paper>
    </Box>
  );
};

export default ChatInterface;
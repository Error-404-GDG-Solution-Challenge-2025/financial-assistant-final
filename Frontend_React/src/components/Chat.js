import React, { useState } from 'react';
import { Box, CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import ChatInterface from './ChatInterface';
import Sidebar from './Sidebar';
import axios from 'axios';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#10a37f',
    },
    background: {
      default: '#343541',
      paper: '#444654',
    },
  },
  typography: {
    fontFamily: "'Söhne', 'Helvetica Neue', 'Arial', sans-serif",
  },
});

function Chat() {
  const [chats, setChats] = useState([
    { id: 1, title: 'Welcome Chat', messages: [] }
  ]);
  const [activeChat, setActiveChat] = useState(1);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [ai_response, setAi_response] = useState("");

  const handleNewChat = () => {
    const newChat = {
      id: Date.now(),
      title: `New Chat`,
      messages: []
    };
    setChats([...chats, newChat]);
    setActiveChat(newChat.id);
  };

  const handleDeleteChat = (chatId) => {
    const newChats = chats.filter(chat => chat.id !== chatId);
    setChats(newChats);
    if (activeChat === chatId) {
      setActiveChat(newChats[0]?.id || null);
    }
  };

  const handleSendMessage = (message) => {
    const currentChat = chats.find(chat => chat.id === activeChat);
    if (!currentChat) return;

    const updatedChat = {
      ...currentChat,
      messages: [
        ...currentChat.messages,
        { role: 'user', content: message }
      ]
    };

    // Call the python backend and retrieve the generated response from agent
    axios.post('http://localhost:8000/generate', {
      prompt: message
    }).then(response => {
      console.log("AI Response:", response.data);
      setAi_response(response.data.generated_text);

      // Update the chat with the AI response
      setChats(prevChats => prevChats.map(chat =>
        chat.id === activeChat ? {
          ...chat,
          messages: [...chat.messages, { role: 'assistant', content: response.data.generated_text }]
        } : chat
      ));
    }).catch(error => {
      console.error("Error calling API:", error);
      // Handle error by showing a message to the user
      setChats(prevChats => prevChats.map(chat =>
        chat.id === activeChat ? {
          ...chat,
          messages: [...chat.messages, { role: 'assistant', content: "Sorry, I couldn't process your request. Please try again." }]
        } : chat
      ));
    });

    // Update chat title if it's the first message
    if (currentChat.messages.length === 0) {
      updatedChat.title = message.slice(0, 30) + (message.length > 30 ? '...' : '');
    }

    setChats(chats.map(chat =>
      chat.id === activeChat ? updatedChat : chat
    ));

    // Remove the setTimeout simulation since we're using the real API now
  };

  const currentChat = chats.find(chat => chat.id === activeChat);

  chats.map(chat => console.log("MESSAGES: ", chat.messages));
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>

        <Sidebar
          open={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
          onNewChat={handleNewChat}
          chats={chats}
          onDeleteChat={handleDeleteChat}
          activeChat={activeChat}
          onSelectChat={setActiveChat}
        />
        <ChatInterface
          messages={currentChat?.messages || []}
          onSendMessage={handleSendMessage}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        />
      </Box>
    </ThemeProvider>
  );
}

export default Chat;

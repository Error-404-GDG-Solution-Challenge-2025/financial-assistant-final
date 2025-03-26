import React from 'react';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Typography,
  Divider,
  Tooltip,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import ChatIcon from '@mui/icons-material/Chat';
import CloseIcon from '@mui/icons-material/Close';
import DeleteIcon from '@mui/icons-material/Delete';

const drawerWidth = 260;

const Sidebar = ({ open, onClose, onNewChat, chats = [], onDeleteChat, activeChat, onSelectChat }) => {
  return (
    <Drawer
      variant="temporary"
      anchor="left"
      open={open}
      onClose={onClose}
      ModalProps={{
        keepMounted: true, // Better performance on mobile
      }}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          backgroundColor: '#202123',
          color: 'white',
          transition: 'transform 0.3s ease-in-out',
        },
      }}
    >
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" noWrap component="div">
          Financial Assistant
        </Typography>
        <IconButton onClick={onClose} sx={{ display: { sm: 'none' }, color: 'white' }}>
          <CloseIcon />
        </IconButton>
      </Box>
      <Divider sx={{ borderColor: 'rgba(255,255,255,0.1)' }} />
      <Box sx={{ p: 2 }}>
        <ListItemButton
          onClick={onNewChat}
          sx={{
            borderRadius: 1,
            border: '1px solid rgba(255,255,255,0.2)',
            '&:hover': {
              backgroundColor: 'rgba(255,255,255,0.1)',
            },
          }}
        >
          <ListItemIcon sx={{ color: 'white' }}>
            <AddIcon />
          </ListItemIcon>
          <ListItemText primary="New Chat" sx={{ color: 'white' }} />
        </ListItemButton>
      </Box>
      <Divider sx={{ borderColor: 'rgba(255,255,255,0.1)' }} />
      <List sx={{ flexGrow: 1, overflow: 'auto' }}>
        {chats.map((chat, index) => (
          <ListItem 
            key={chat.id} 
            disablePadding
            secondaryAction={
              <Tooltip title="Delete chat">
                <IconButton 
                  edge="end" 
                  sx={{ color: 'rgba(255,255,255,0.5)' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteChat(chat.id);
                  }}
                >
                  <DeleteIcon />
                </IconButton>
              </Tooltip>
            }
            sx={{
              backgroundColor: activeChat === chat.id ? 'rgba(255,255,255,0.1)' : 'transparent',
            }}
          >
            <ListItemButton
              onClick={() => onSelectChat(chat.id)}
              sx={{
                '&:hover': {
                  backgroundColor: 'rgba(255,255,255,0.1)',
                },
              }}
            >
              <ListItemIcon sx={{ color: 'white' }}>
                <ChatIcon />
              </ListItemIcon>
              <ListItemText 
                primary={chat.title || `Chat ${index + 1}`}
                sx={{ 
                  color: 'white',
                  '& .MuiListItemText-primary': {
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }
                }} 
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
};

export default Sidebar;

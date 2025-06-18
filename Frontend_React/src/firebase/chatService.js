import { db } from './index';
import { collection, doc, getDocs, addDoc, deleteDoc } from 'firebase/firestore';

// Get all chats for a user
export const getUserChats = async (userId) => {
  const chatsRef = collection(db, 'users', userId, 'chats');
  const snapshot = await getDocs(chatsRef);
  return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
};

// Create a new chat
export const createChat = async (userId, title = 'New Chat') => {
  const chatsRef = collection(db, 'users', userId, 'chats');
  const newChatRef = await addDoc(chatsRef, { title });
  return { id: newChatRef.id, title };
};

// Delete a chat
export const deleteChat = async (userId, chatId) => {
  await deleteDoc(doc(db, 'users', userId, 'chats', chatId));
};

// Get all messages for a chat
export const getChatMessages = async (userId, chatId) => {
  const messagesRef = collection(db, 'users', userId, 'chats', chatId, 'messages');
  const snapshot = await getDocs(messagesRef);
  return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
};

// Add a message to a chat
export const addMessage = async (userId, chatId, { sender, content }) => {
  const messagesRef = collection(db, 'users', userId, 'chats', chatId, 'messages');
  await addDoc(messagesRef, { sender, content });
};
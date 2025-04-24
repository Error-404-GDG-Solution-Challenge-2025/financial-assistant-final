import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import './styles/App.css';

// Component imports
import LoginModal from './components/LoginModal';
import ChatPage from './components/ChatPage';
import { auth } from './firebase';
import { onAuthStateChanged } from 'firebase/auth';

function App() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const openModal = () => {
    setIsModalOpen(true);
    document.body.style.overflow = 'hidden';
  };

  const closeModal = () => {
    setIsModalOpen(false);
    document.body.style.overflow = '';
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <Router>
      <AppContent 
        openModal={openModal} 
        isModalOpen={isModalOpen} 
        closeModal={closeModal}
        user={user}
      />
    </Router>
  );
}

function AppContent({ openModal, isModalOpen, closeModal, user }) {
  const location = useLocation();
  const isChatPage = location.pathname === "/chat";

  // Remove the unused state and handler function
  // const [isSidebarOpen, setIsSidebarOpen] = useState(false); // REMOVED
  // const handleToggleSidebar = () => { // REMOVED
  //   setIsSidebarOpen(!isSidebarOpen); // REMOVED
  // }; // REMOVED

  return (
    <div className="App">
      {!isChatPage && <Navbar user={user} openModal={openModal} />}

      <main>
        <Routes>
          <Route
            path="/"
            element={user ? <ChatPage user={user} /> : <Navigate to="/login" />}
          />
          <Route
            path="/login"
            element={
              user ? (
                <Navigate to="/" />
              ) : (
                <div className="login-container">
                  <h1>AI Chat Assistant</h1>
                  <button onClick={openModal} className="login-button">
                    Login to continue
                  </button>
                </div>
              )
            }
          />
        </Routes>
        
        <LoginModal isOpen={isModalOpen} onClose={closeModal} />
      </div>
    </Router>
  );
}

export default App;

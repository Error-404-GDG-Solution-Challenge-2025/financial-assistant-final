import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, useLocation, Navigate } from 'react-router-dom';
import './styles/App.css';

// Component imports
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Services from './components/Services';
import Footer from './components/Footer';
import LoginModal from './components/LoginModal';
import Chat from './components/Chat';
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

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const handleToggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="App">
      {!isChatPage && <Navbar user={user} openModal={openModal} />}
      
      <main>
        <Routes>
          <Route
            path="/"
            element={
              <>
                <Hero openModal={openModal} />
                <Services />
              </>
            }
          />
          <Route path="/services" element={<Services />} />
          <Route 
            path="/chat" 
            element={user ? <Chat /> : <Navigate to="/" />} 
          />
        </Routes>
      </main>

      {!isChatPage && <Footer />}
      
      <LoginModal isOpen={isModalOpen} onClose={closeModal} />
    </div>
  );
}

export default App;

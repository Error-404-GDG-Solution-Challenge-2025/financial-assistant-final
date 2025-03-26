// components/LoginModal.js
import React, { useState } from 'react';
import { auth, db } from '../firebase';
import { createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from 'firebase/auth';
import { doc, setDoc } from 'firebase/firestore';
import { useNavigate } from 'react-router-dom';

const LoginModal = ({ isOpen, onClose }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: ''
  });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevState => ({
      ...prevState,
      [name]: value
    }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      if (isLogin) {
        // Login
        await signInWithEmailAndPassword(auth, formData.email, formData.password);
        onClose();
        navigate('/chat');
      } else {
        // Sign up
        if (formData.password !== formData.confirmPassword) {
          setError('Passwords do not match');
          return;
        }
        
        // Create user in Firebase Auth
        const userCredential = await createUserWithEmailAndPassword(
          auth, 
          formData.email, 
          formData.password
        );

        // Store additional user data in Firestore
        await setDoc(doc(db, 'users', userCredential.user.uid), {
          name: formData.name,
          email: formData.email,
          createdAt: new Date().toISOString(),
          lastLogin: new Date().toISOString()
        });

        onClose();
        navigate('/chat');
      }
    } catch (error) {
      setError(error.message);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
      onClose();
      navigate('/');
    } catch (error) {
      setError(error.message);
    }
  };

  return (
    <div className={`modal-overlay ${isOpen ? 'active' : ''}`} id="loginModal">
      <div className="login-modal">
        <button className="close-modal" aria-label="Close modal" onClick={onClose}>&times;</button>
        <h2>{isLogin ? 'Login to Your Account' : 'Create New Account'}</h2>
        {error && <div className="error-message">{error}</div>}
        <form className="login-form" id="loginForm" onSubmit={handleSubmit}>
          {!isLogin && (
            <input 
              type="text" 
              className="form-input" 
              placeholder="Full Name" 
              name="name"
              required 
              value={formData.name}
              onChange={handleChange}
            />
          )}
          <input 
            type="email" 
            className="form-input" 
            placeholder="Email" 
            name="email"
            required 
            value={formData.email}
            onChange={handleChange}
          />
          <input 
            type="password" 
            className="form-input" 
            placeholder="Password" 
            name="password"
            required 
            value={formData.password}
            onChange={handleChange}
          />
          {!isLogin && (
            <input 
              type="password" 
              className="form-input" 
              placeholder="Confirm Password" 
              name="confirmPassword"
              required 
              value={formData.confirmPassword}
              onChange={handleChange}
            />
          )}
          <button type="submit" className="login-button">
            {isLogin ? 'Login' : 'Sign Up'}
          </button>
        </form>
        <div className="login-options">
          <p>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button 
              className="link-button" 
              onClick={() => setIsLogin(!isLogin)}
            >
              {isLogin ? 'Sign up' : 'Login'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginModal;
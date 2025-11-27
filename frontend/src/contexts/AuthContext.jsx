import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useNotification } from './NotificationContext';
import { getToken, getUser, login as authLogin, signup as authSignup, logout as authLogout } from '../services/auth';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);


export const AuthProvider = ({ children }) => {

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  

  const navigate = useNavigate();
  const { addGlobalNotification, addFormNotification } = useNotification();

  useEffect(() => {

    const initAuth = () => {

      const token = getToken();
      if (token) {
        const user = getUser();
        setUser(user);
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  const login = async (email, password) => {

    try {

      const result = await authLogin(email, password);
      const user = getUser();
      setUser(user);
      navigate('/chat');
      return { success: true };
    } catch (error) {
      const message = error.message || 'We had trouble signing you in. Please check your credentials and try again.';
      addFormNotification(message, 'error');
      return { success: false, message };
    }
  };

  const signup = async (userData) => {

    try {

      const result = await authSignup(userData.email, userData.password, userData.fullName);
      addGlobalNotification('Welcome! Your account has been created successfully.', 'success');
      return { success: true };
    } catch (error) {
      const message = error.message || 'We had trouble creating your account. Please try again.';
      addFormNotification(message, 'error');
      return { success: false, message };
    }
  };

  const logout = () => {

    authLogout();
    setUser(null);
    addGlobalNotification('You have been logged out successfully. Come back soon!', 'success');
    navigate('/');
  };

  const value = {
    user,
    loading,
    login,
    signup,
    logout,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
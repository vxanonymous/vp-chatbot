import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider, useNotification } from './contexts/NotificationContext';
import Notification from './components/Notification';
import ProtectedRoute from './components/ProtectedRoute';
import LandingPage from './pages/LandingPage';
import AuthPage from './pages/AuthPage';
import ChatPage from './pages/ChatPage';
import './App.css';

/**
 * Vacation Planning System - Main Application Component
 * 
 * This is where everything starts - it sets up the whole app structure.
 * Handles routing, authentication, notifications, and the dark/light mode toggle.
 */

function AppContent() {

  const [darkMode, setDarkMode] = useState(() => {
    const savedPreference = localStorage.getItem('darkMode');
    if (savedPreference !== null) {
      return savedPreference === 'true';
    }

    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });


  useEffect(() => {

    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', darkMode);
  }, [darkMode]);


  const toggleDarkMode = () => setDarkMode((prev) => !prev);



  const { notifications, removeNotification } = useNotification();

  return (
    <BrowserRouter>
      <AuthProvider>
        <Notification notifications={notifications} onDismiss={removeNotification} />
        <div className="min-h-screen w-full bg-gray-50 dark:bg-gray-900 flex flex-col">
          {/* Dark mode toggle - let them switch between light and dark */}
          <button
            onClick={toggleDarkMode}
            className="fixed bottom-4 right-4 z-50 px-3 py-1 rounded bg-gray-200 dark:bg-gray-800 text-gray-800 dark:text-gray-200 border border-gray-300 dark:border-gray-700 shadow hover:bg-gray-300 dark:hover:bg-gray-700 transition"
            aria-label="Toggle dark mode"
          >
            {darkMode ? '🌙 Dark' : '☀️ Light'}
          </button>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/auth" element={<AuthPage />} />
            <Route
              path="/chat"
              element={
                <ProtectedRoute>
                  <ChatPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/chat/:conversationId"
              element={
                <ProtectedRoute>
                  <ChatPage />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}

function App() {
  return (
    <NotificationProvider>
      <AppContent />
    </NotificationProvider>
  );
}

export default App;
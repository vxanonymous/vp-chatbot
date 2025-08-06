import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  // Show a loading spinner while we check if they're logged in
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Send them to login if they're not logged in
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }

  // Show the page if they're logged in
  return children;
};

export default ProtectedRoute;
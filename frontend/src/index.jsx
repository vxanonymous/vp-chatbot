import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App.jsx';

/**
 * React Application Entry Point
 * 
 * This is the main entry point for the Vacation Planning System React application.
 * It initializes React and renders the main App component into the DOM.
 */

// Initialize React application
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
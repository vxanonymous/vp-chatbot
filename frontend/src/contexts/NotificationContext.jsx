import React, { createContext, useContext, useState, useCallback } from 'react';

const NotificationContext = createContext();

export const useNotification = () => useContext(NotificationContext);

export const NotificationProvider = ({ children }) => {
  // Keep track of all the notifications we want to show
  const [notifications, setNotifications] = useState([]);

  const addNotification = useCallback((message, type = 'info', options = {}) => {
    // Create a unique ID for this notification
    const id = Date.now() + Math.random();
    const notification = {
      id,
      message,
      type,
      position: options.position || 'top-right', // top-right, inline, form
      dismissible: options.dismissible !== false, // default to true
      autoDismiss: options.autoDismiss !== false, // default to true
      duration: options.duration || 5000, // 5 seconds default
      ...options
    };
    
    setNotifications((prev) => [...prev, notification]);
    
    // Make the notification disappear after a while
    if (notification.autoDismiss && notification.duration > 0) {
      setTimeout(() => {
        removeNotification(id);
      }, notification.duration);
    }
    
    return id;
  }, []);

  const removeNotification = useCallback((id) => {
    // Get rid of a specific notification
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const clearNotifications = useCallback((position = null) => {
    // Clear notifications by where they appear, or all of them
    if (position) {
      setNotifications((prev) => prev.filter((n) => n.position !== position));
    } else {
      setNotifications([]);
    }
  }, []);

  const addGlobalNotification = useCallback((message, type = 'info') => {
    // Show a notification in the top-right corner
    return addNotification(message, type, { position: 'top-right' });
  }, [addNotification]);

  const addInlineNotification = useCallback((message, type = 'info') => {
    // Show a notification that stays until they dismiss it
    return addNotification(message, type, { 
      position: 'inline', 
      dismissible: true,
      autoDismiss: false 
    });
  }, [addNotification]);

  const addFormNotification = useCallback((message, type = 'error') => {
    // Show a notification for form errors
    return addNotification(message, type, { 
      position: 'form', 
      dismissible: true,
      autoDismiss: false 
    });
  }, [addNotification]);

  return (
    <NotificationContext.Provider value={{ 
      notifications, 
      addNotification, 
      removeNotification, 
      clearNotifications,
      addGlobalNotification,
      addInlineNotification,
      addFormNotification
    }}>
      {children}
    </NotificationContext.Provider>
  );
}; 
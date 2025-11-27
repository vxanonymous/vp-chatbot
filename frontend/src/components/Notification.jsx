import React from 'react';
import { createPortal } from 'react-dom';
import { CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';

const Notification = ({ notifications = [], onDismiss }) => {

  if (typeof window === 'undefined' || !notifications || !Array.isArray(notifications) || notifications.length === 0) {
    return null;
  }

  const globalNotifications = notifications.filter(n => n.position === 'top-right');
  const inlineNotifications = notifications.filter(n => n.position === 'inline');
  const formNotifications = notifications.filter(n => n.position === 'form');

  const getIcon = (type) => {

    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getNotificationClasses = (type, position) => {

    const baseClasses = "flex items-center justify-between px-4 py-3 rounded-lg shadow-lg min-w-[280px] max-w-xs border transition-all duration-300";
    
    switch (type) {
      case 'success':
        return `${baseClasses} bg-green-50 dark:bg-green-900 text-green-900 dark:text-green-100 border-green-200 dark:border-green-700`;
      case 'error':
        return `${baseClasses} bg-red-50 dark:bg-red-900 text-red-900 dark:text-red-100 border-red-200 dark:border-red-700`;
      case 'warning':
        return `${baseClasses} bg-yellow-50 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100 border-yellow-200 dark:border-yellow-700`;
      default:
        return `${baseClasses} bg-gray-900 dark:bg-gray-800 text-white dark:text-gray-100 border-gray-700 dark:border-gray-600`;
    }
  };

  const renderNotification = (notification) => (
    <div
      key={notification?.id || Math.random()}
      className={`${getNotificationClasses(notification?.type, notification?.position)} pointer-events-auto`}
    >
      <div className="flex items-center flex-1 mr-3">
        {getIcon(notification?.type)}
        <span className="ml-2 text-sm">{notification?.message || ''}</span>
      </div>
      {notification?.dismissible && (
        <button
          onClick={() => onDismiss && onDismiss(notification?.id)}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-opacity-50 rounded-full w-6 h-6 flex items-center justify-center text-lg font-bold transition-colors"
          aria-label="Dismiss notification"
        >
          ×
        </button>
      )}
    </div>
  );

  const portalTarget = document.body;

  return createPortal(
    <div className="pointer-events-none">
      {globalNotifications.length > 0 && (
        <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 items-end">
          {globalNotifications.map(renderNotification)}
        </div>
      )}

      {inlineNotifications.length > 0 && (
        <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 items-end" style={{ marginTop: `${globalNotifications.length * 60}px` }}>
          {inlineNotifications.map(renderNotification)}
        </div>
      )}

      {formNotifications.length > 0 && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 z-40 flex flex-col gap-2 items-center max-w-lg w-full px-4">
          {formNotifications.map(renderNotification)}
        </div>
      )}
    </div>,
    portalTarget
  );
};

export default Notification; 
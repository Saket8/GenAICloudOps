import React, { useRef, useEffect } from 'react';
import { useNotifications, Notification } from '../../contexts/NotificationContext';

interface NotificationPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function NotificationPanel({ isOpen, onClose }: NotificationPanelProps) {
  const { notifications, unreadCount, markAsRead, markAllAsRead, removeNotification, clearAll } = useNotifications();
  const panelRef = useRef<HTMLDivElement>(null);

  // Close panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  const getNotificationIcon = (type: Notification['type']) => {
    switch (type) {
      case 'error':
        return 'fas fa-exclamation-circle text-red-500';
      case 'warning':
        return 'fas fa-exclamation-triangle text-yellow-500';
      case 'success':
        return 'fas fa-check-circle text-green-500';
      case 'info':
      default:
        return 'fas fa-info-circle text-blue-500';
    }
  };

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays}d ago`;
  };

  if (!isOpen) return null;

  return (
    <div className="absolute top-12 right-0 w-96 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50" ref={panelRef}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Notifications
          {unreadCount > 0 && (
            <span className="ml-2 px-2 py-1 text-xs bg-red-500 text-white rounded-full">
              {unreadCount}
            </span>
          )}
        </h3>
        <div className="flex space-x-2">
          {notifications.length > 0 && (
            <>
              <button
                onClick={markAllAsRead}
                className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
                disabled={unreadCount === 0}
              >
                Mark all read
              </button>
              <button
                onClick={clearAll}
                className="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
              >
                Clear all
              </button>
            </>
          )}
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <i className="fas fa-times"></i>
          </button>
        </div>
      </div>

      {/* Notifications List */}
      <div className="max-h-96 overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
            <i className="fas fa-bell-slash text-3xl mb-4"></i>
            <p>No notifications</p>
            <p className="text-xs mt-1">You're all caught up!</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                  !notification.read ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-1">
                    <i className={getNotificationIcon(notification.type)}></i>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {notification.title}
                      </h4>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {formatTimestamp(notification.timestamp)}
                        </span>
                        <button
                          onClick={() => removeNotification(notification.id)}
                          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                        >
                          <i className="fas fa-times text-xs"></i>
                        </button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                      {notification.message}
                    </p>
                    
                    <div className="flex items-center justify-between mt-2">
                      <div className="flex items-center space-x-2">
                        {notification.resourceType && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                            {notification.resourceType}
                          </span>
                        )}
                        {!notification.read && (
                          <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                        )}
                      </div>
                      
                      <div className="flex space-x-2">
                        {!notification.read && (
                          <button
                            onClick={() => markAsRead(notification.id)}
                            className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
                          >
                            Mark read
                          </button>
                        )}
                        {notification.actionable && (
                          <button className="text-xs text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200">
                            Take Action
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {notifications.length > 0 && (
        <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 rounded-b-lg">
          <button className="w-full text-center text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200">
            View All Notifications
          </button>
        </div>
      )}
    </div>
  );
} 
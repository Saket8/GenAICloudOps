import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import { NotificationPanel } from '../ui/NotificationPanel';
import { useTheme } from '../../contexts/ThemeContext';

interface HeaderProps {
  user?: any;
  onMenuClick: () => void;
  onChatbotToggle: () => void;
}

export function Header({ user, onMenuClick, onChatbotToggle }: HeaderProps) {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { unreadCount } = useNotifications();
  const { theme, toggleTheme } = useTheme();
  const [notificationPanelOpen, setNotificationPanelOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <header
      className="relative z-40 shadow-xl border-b border-blue-900/30 overflow-hidden"
      style={{
        background: 'linear-gradient(to right, #000000 0%, #050d1a 10%, #0c1a30 20%, #122545 30%, #183060 40%, #1e3b7a 50%, #2446a0 70%, #1e4fc2 100%)'
      }}
    >
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">

          {/* Left Section */}
          <div className="flex items-center">
            {/* Mobile menu button */}
            <button
              onClick={onMenuClick}
              className="md:hidden p-2 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-all"
            >
              <i className="fas fa-bars text-lg" />
            </button>

            {/* Cognizant Logo and Title */}
            <div className="flex items-center ml-4 md:ml-0">
              {/* Cognizant Logo - Using new gradient logo */}
              <div className="flex-shrink-0 mr-4 px-2 py-1">
                <img
                  src="/cognizant-logo.jpg"
                  alt="Cognizant"
                  className="h-14 w-auto object-contain"
                />
              </div>

              {/* Divider */}
              <div className="hidden sm:block h-8 w-px bg-gradient-to-b from-transparent via-white/30 to-transparent mr-4" />

              {/* Application Title */}
              <div>
                <h1 className="text-xl font-bold text-white tracking-tight">
                  GenAI CloudOps
                </h1>
                <p className="text-xs text-blue-200/80 font-medium">
                  Cloud Operations Dashboard
                </p>
              </div>
            </div>
          </div>

          {/* Center Section - Enhanced Search */}
          <div className="hidden md:flex flex-1 max-w-lg mx-8">
            <div className="w-full relative group">
              <input
                type="search"
                placeholder="Search resources, compartments, or alerts..."
                className="w-full pl-11 pr-4 py-2.5 text-sm bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl focus:ring-2 focus:ring-blue-400/50 focus:border-blue-400/50 focus:bg-white/15 text-white placeholder-blue-200/60 transition-all duration-200"
              />
              <i className="fas fa-search absolute left-4 top-1/2 transform -translate-y-1/2 text-blue-200/60 group-focus-within:text-blue-300 transition-colors" />
            </div>
          </div>

          {/* Right Section */}
          <div className="flex items-center space-x-2">

            {/* Home Button */}
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2.5 text-blue-200/80 hover:text-white hover:bg-white/10 rounded-xl transition-all duration-200"
              title="Go to Dashboard"
            >
              <i className="fas fa-home text-lg" />
            </button>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2.5 text-blue-200/80 hover:text-white hover:bg-white/10 rounded-xl transition-all duration-200"
              title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            >
              {theme === 'light' ? (
                <i className="fas fa-moon text-lg" />
              ) : (
                <i className="fas fa-sun text-lg text-yellow-400" />
              )}
            </button>

            {/* Notifications */}
            <div className="relative">
              <button
                onClick={() => setNotificationPanelOpen(!notificationPanelOpen)}
                className="p-2.5 text-blue-200/80 hover:text-white hover:bg-white/10 rounded-xl transition-all duration-200 relative"
                title="Notifications"
              >
                <i className="fas fa-bell text-lg" />
                {unreadCount > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 flex h-5 w-5 items-center justify-center">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-4 w-4 bg-gradient-to-r from-red-500 to-rose-500 text-white text-[10px] font-bold items-center justify-center shadow-lg">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  </span>
                )}
              </button>

              <NotificationPanel
                isOpen={notificationPanelOpen}
                onClose={() => setNotificationPanelOpen(false)}
              />
            </div>

            {/* Chatbot Toggle */}
            <button
              onClick={onChatbotToggle}
              className="p-2.5 text-blue-200/80 hover:text-white hover:bg-white/10 rounded-xl transition-all duration-200 relative group"
              title="Toggle AI Assistant"
            >
              <i className="fas fa-robot text-lg" />
              {/* Active indicator */}
              <span className="absolute bottom-1 right-1 w-2 h-2 bg-green-400 rounded-full border border-[#0d1b4c] group-hover:animate-pulse" />
            </button>

            {/* Divider */}
            <div className="h-8 w-px bg-white/20 mx-2" />

            {/* User Menu */}
            <div className="relative">
              <div className="flex items-center space-x-3">
                {/* User Avatar */}
                <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center shadow-lg ring-2 ring-white/20">
                  <span className="text-sm font-bold text-white">
                    {user?.full_name?.charAt(0)?.toUpperCase() || user?.username?.charAt(0)?.toUpperCase() || 'U'}
                  </span>
                </div>

                {/* User Info */}
                <div className="hidden md:block">
                  <p className="text-sm font-semibold text-white">
                    {user?.full_name || user?.username || 'User'}
                  </p>
                  <p className="text-xs text-blue-200/70">
                    Administrator
                  </p>
                </div>

                {/* Logout Button */}
                <button
                  onClick={handleLogout}
                  className="p-2 text-blue-200/80 hover:text-white hover:bg-red-500/20 rounded-xl transition-all duration-200"
                  title="Logout"
                >
                  <i className="fas fa-sign-out-alt text-lg" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
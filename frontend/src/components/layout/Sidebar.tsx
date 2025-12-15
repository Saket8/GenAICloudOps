import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
      onClose();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const quickActions = [
    { name: 'View All Resources', path: '/cloud-resources', icon: 'fas fa-list' },
    { name: 'System Health', path: '/monitoring/health', icon: 'fas fa-heartbeat' },
    { name: 'Cost Overview', path: '/cost-analysis', icon: 'fas fa-chart-pie' },
    { name: 'Recent Alerts', path: '/monitoring/alerts', icon: 'fas fa-exclamation-triangle' },
  ];

  const supportLinks = [
    { name: 'Documentation', href: '#', icon: 'fas fa-book' },
    { name: 'API Reference', href: '#', icon: 'fas fa-code' },
    { name: 'Support', href: '#', icon: 'fas fa-life-ring' },
    { name: 'Feedback', href: '#', icon: 'fas fa-comment' },
  ];

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-gradient-to-b from-[#0d1b4c] via-[#0f2167] to-[#1a3a8f] shadow-2xl transform transition-transform duration-300 ease-in-out md:hidden ${isOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
      >
        <div className="flex flex-col h-full">

          {/* Header with Cognizant Logo */}
          <div className="relative p-5 border-b border-white/10">
            {/* Background decoration */}
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-transparent" />

            <div className="relative flex items-center justify-between">
              <div className="flex items-center">
                <img
                  src="/cognizant-logo.png"
                  alt="Cognizant"
                  className="h-8 w-auto object-contain"
                  style={{ filter: 'brightness(1.1)' }}
                />
                <div className="ml-3">
                  <span className="text-base font-bold text-white">
                    GenAI CloudOps
                  </span>
                  <p className="text-xs text-blue-200/70">Cloud Dashboard</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-xl text-white/60 hover:text-white hover:bg-white/10 transition-all"
              >
                <i className="fas fa-times text-lg" />
              </button>
            </div>
          </div>

          {/* User Info */}
          <div className="p-5 border-b border-white/10">
            <div className="flex items-center">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center shadow-lg ring-2 ring-white/20">
                <span className="text-lg font-bold text-white">
                  {user?.full_name?.charAt(0)?.toUpperCase() || user?.username?.charAt(0)?.toUpperCase() || 'U'}
                </span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-white">
                  {user?.full_name || user?.username || 'User'}
                </p>
                <p className="text-xs text-blue-200/60">
                  {user?.email || 'No email'}
                </p>
              </div>
            </div>
          </div>

          {/* Navigation Content */}
          <div className="flex-1 overflow-y-auto py-4">

            {/* Quick Actions */}
            <div className="px-4 mb-6">
              <h3 className="text-xs font-bold text-blue-200/50 uppercase tracking-wider mb-3 px-2">
                Quick Actions
              </h3>
              <nav className="space-y-1">
                {quickActions.map((action) => (
                  <NavLink
                    key={action.name}
                    to={action.path}
                    onClick={onClose}
                    className="group flex items-center px-3 py-2.5 text-sm font-medium rounded-xl text-blue-100/80 hover:bg-white/10 hover:text-white transition-all duration-200"
                  >
                    <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center mr-3 group-hover:bg-white/20 transition-colors">
                      <i className={`${action.icon} text-sm text-blue-200 group-hover:text-white`} />
                    </div>
                    {action.name}
                  </NavLink>
                ))}
              </nav>
            </div>

            {/* Support Links */}
            <div className="px-4">
              <h3 className="text-xs font-bold text-blue-200/50 uppercase tracking-wider mb-3 px-2">
                Support & Help
              </h3>
              <nav className="space-y-1">
                {supportLinks.map((link) => (
                  <a
                    key={link.name}
                    href={link.href}
                    className="group flex items-center px-3 py-2.5 text-sm font-medium rounded-xl text-blue-100/80 hover:bg-white/10 hover:text-white transition-all duration-200"
                  >
                    <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center mr-3 group-hover:bg-white/20 transition-colors">
                      <i className={`${link.icon} text-sm text-blue-200 group-hover:text-white`} />
                    </div>
                    {link.name}
                  </a>
                ))}
              </nav>
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-white/10">
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center px-4 py-3 text-sm font-semibold rounded-xl text-white bg-red-500/20 hover:bg-red-500/30 border border-red-400/30 hover:border-red-400/50 transition-all duration-200"
            >
              <i className="fas fa-sign-out-alt mr-2" />
              Sign out
            </button>

            {/* Powered by */}
            <div className="mt-4 text-center">
              <p className="text-xs text-blue-200/40">Powered by</p>
              <img
                src="/cognizant-logo.png"
                alt="Cognizant"
                className="h-5 w-auto mx-auto mt-1 opacity-50"
              />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
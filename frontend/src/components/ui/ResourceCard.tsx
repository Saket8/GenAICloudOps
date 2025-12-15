import React, { useState } from 'react';

interface Resource {
  id: string;
  name?: string;
  display_name?: string;
  lifecycle_state: string;
  [key: string]: any;
}

interface ResourceCardProps {
  title: string;
  icon: string;
  color: 'blue' | 'green' | 'purple' | 'orange' | 'indigo' | 'red' | 'yellow';
  resources: Resource[];
  resourceType: string;
}

export function ResourceCard({ title, icon, color, resources, resourceType }: ResourceCardProps) {
  const [expanded, setExpanded] = useState(false);

  // Premium color configurations with gradients
  const colorConfig = {
    blue: {
      gradient: 'from-blue-500 to-blue-600',
      bgGlow: 'bg-blue-500',
      text: 'text-blue-600 dark:text-blue-400',
      badge: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border-blue-100 dark:border-blue-800',
      ring: 'ring-blue-500/20',
    },
    green: {
      gradient: 'from-emerald-500 to-teal-600',
      bgGlow: 'bg-emerald-500',
      text: 'text-emerald-600 dark:text-emerald-400',
      badge: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300 border-emerald-100 dark:border-emerald-800',
      ring: 'ring-emerald-500/20',
    },
    purple: {
      gradient: 'from-purple-500 to-violet-600',
      bgGlow: 'bg-purple-500',
      text: 'text-purple-600 dark:text-purple-400',
      badge: 'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 border-purple-100 dark:border-purple-800',
      ring: 'ring-purple-500/20',
    },
    orange: {
      gradient: 'from-orange-500 to-amber-600',
      bgGlow: 'bg-orange-500',
      text: 'text-orange-600 dark:text-orange-400',
      badge: 'bg-orange-50 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300 border-orange-100 dark:border-orange-800',
      ring: 'ring-orange-500/20',
    },
    indigo: {
      gradient: 'from-indigo-500 to-blue-600',
      bgGlow: 'bg-indigo-500',
      text: 'text-indigo-600 dark:text-indigo-400',
      badge: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 border-indigo-100 dark:border-indigo-800',
      ring: 'ring-indigo-500/20',
    },
    red: {
      gradient: 'from-red-500 to-rose-600',
      bgGlow: 'bg-red-500',
      text: 'text-red-600 dark:text-red-400',
      badge: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300 border-red-100 dark:border-red-800',
      ring: 'ring-red-500/20',
    },
    yellow: {
      gradient: 'from-yellow-500 to-amber-600',
      bgGlow: 'bg-yellow-500',
      text: 'text-yellow-600 dark:text-yellow-400',
      badge: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300 border-yellow-100 dark:border-yellow-800',
      ring: 'ring-yellow-500/20',
    }
  };

  const config = colorConfig[color];

  const getHealthStatus = (resource: Resource) => {
    const state = resource.lifecycle_state?.toUpperCase();
    if (['ACTIVE', 'RUNNING', 'AVAILABLE'].includes(state)) {
      return { status: 'healthy', color: 'text-emerald-500', bgColor: 'bg-emerald-500', icon: 'fa-check-circle', label: 'Active' };
    } else if (['STOPPED', 'INACTIVE'].includes(state)) {
      return { status: 'stopped', color: 'text-amber-500', bgColor: 'bg-amber-500', icon: 'fa-pause-circle', label: 'Stopped' };
    } else if (['FAILED', 'ERROR', 'TERMINATED'].includes(state)) {
      return { status: 'error', color: 'text-red-500', bgColor: 'bg-red-500', icon: 'fa-exclamation-circle', label: 'Error' };
    } else {
      return { status: 'unknown', color: 'text-gray-400', bgColor: 'bg-gray-400', icon: 'fa-question-circle', label: 'Unknown' };
    }
  };

  const healthyCount = resources.filter(r => ['ACTIVE', 'RUNNING', 'AVAILABLE'].includes(r.lifecycle_state?.toUpperCase())).length;
  const stoppedCount = resources.filter(r => ['STOPPED', 'INACTIVE'].includes(r.lifecycle_state?.toUpperCase())).length;
  const errorCount = resources.filter(r => ['FAILED', 'ERROR', 'TERMINATED'].includes(r.lifecycle_state?.toUpperCase())).length;

  // Calculate health percentage
  const healthPercentage = resources.length > 0 ? Math.round((healthyCount / resources.length) * 100) : 0;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-xl hover:border-gray-200 dark:hover:border-gray-600 transition-all duration-300 group relative overflow-hidden">
      {/* Background Glow Effect */}
      <div className={`absolute top-0 right-0 w-32 h-32 ${config.bgGlow} rounded-full mix-blend-multiply filter blur-3xl opacity-5 group-hover:opacity-10 transition-opacity duration-300`} />

      <div className="p-6 relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            {/* Gradient Icon */}
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${config.gradient} flex items-center justify-center shadow-lg group-hover:scale-110 group-hover:shadow-xl transition-all duration-300`}>
              <i className={`${icon} text-white text-lg`} />
            </div>
            <div className="ml-4">
              <h3 className="text-base font-bold text-gray-900 dark:text-white">
                {title}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {resources.length} {resources.length === 1 ? 'resource' : 'resources'}
              </p>
            </div>
          </div>

          {/* Resource Count Badge */}
          <div className={`text-3xl font-bold ${config.text} group-hover:scale-110 transition-transform duration-300`}>
            {resources.length}
          </div>
        </div>

        {/* Health Progress Bar */}
        {resources.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="text-gray-500 dark:text-gray-400 font-medium">Health Score</span>
              <span className={`font-bold ${healthPercentage >= 80 ? 'text-emerald-600' : healthPercentage >= 50 ? 'text-amber-600' : 'text-red-600'}`}>
                {healthPercentage}%
              </span>
            </div>
            <div className="w-full h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-1000 ease-out ${healthPercentage >= 80 ? 'bg-gradient-to-r from-emerald-400 to-emerald-600' :
                    healthPercentage >= 50 ? 'bg-gradient-to-r from-amber-400 to-amber-600' :
                      'bg-gradient-to-r from-red-400 to-red-600'
                  }`}
                style={{ width: `${healthPercentage}%` }}
              />
            </div>
          </div>
        )}

        {/* Health Status Pills */}
        <div className="flex flex-wrap gap-2 mb-4">
          {healthyCount > 0 && (
            <div className="flex items-center px-2.5 py-1 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-100 dark:border-emerald-800 rounded-lg">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-2 animate-pulse" />
              <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-400">{healthyCount} Active</span>
            </div>
          )}
          {stoppedCount > 0 && (
            <div className="flex items-center px-2.5 py-1 bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800 rounded-lg">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mr-2" />
              <span className="text-xs font-semibold text-amber-700 dark:text-amber-400">{stoppedCount} Stopped</span>
            </div>
          )}
          {errorCount > 0 && (
            <div className="flex items-center px-2.5 py-1 bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800 rounded-lg">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 mr-2 animate-pulse" />
              <span className="text-xs font-semibold text-red-700 dark:text-red-400">{errorCount} Error</span>
            </div>
          )}
        </div>

        {/* Empty State */}
        {resources.length === 0 ? (
          <div className="text-center py-8 bg-gray-50 dark:bg-gray-700/30 rounded-xl border border-dashed border-gray-200 dark:border-gray-600">
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${config.gradient} opacity-50 flex items-center justify-center mx-auto mb-3`}>
              <i className={`${icon} text-white`} />
            </div>
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
              No {title.toLowerCase()} found
            </p>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
              Try selecting a different compartment
            </p>
          </div>
        ) : (
          <>
            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-3 text-center">
                <div className="text-xl font-bold text-gray-900 dark:text-white">{healthyCount}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Running</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-3 text-center">
                <div className="text-xl font-bold text-gray-900 dark:text-white">{stoppedCount + errorCount}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Offline</div>
              </div>
            </div>

            {/* Expand Button */}
            <button
              onClick={() => setExpanded(!expanded)}
              className={`w-full flex items-center justify-between px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${expanded
                  ? `bg-gradient-to-r ${config.gradient} text-white shadow-lg`
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
            >
              <span className="flex items-center">
                <i className={`fas fa-list-ul mr-2 text-xs`} />
                View Resources
              </span>
              <i className={`fas fa-chevron-${expanded ? 'up' : 'down'} transition-transform duration-200`} />
            </button>

            {/* Expanded Resource List */}
            {expanded && (
              <div className="mt-4 space-y-2 max-h-64 overflow-y-auto pr-1 custom-scrollbar animate-fadeIn">
                {resources.map((resource, index) => {
                  const health = getHealthStatus(resource);
                  return (
                    <div
                      key={resource.id || index}
                      className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-xl border border-gray-100 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors group/item"
                    >
                      <div className="flex items-center min-w-0 flex-1">
                        {/* Status Indicator */}
                        <div className={`w-8 h-8 rounded-lg ${health.status === 'healthy' ? 'bg-emerald-100 dark:bg-emerald-900/30' : health.status === 'stopped' ? 'bg-amber-100 dark:bg-amber-900/30' : 'bg-red-100 dark:bg-red-900/30'} flex items-center justify-center mr-3 flex-shrink-0`}>
                          <i className={`fas ${health.icon} ${health.color} text-sm`} />
                        </div>
                        <div className="min-w-0 flex-1">
                          <span className="text-sm font-medium text-gray-900 dark:text-white truncate block">
                            {resource.display_name || resource.name || 'Unnamed Resource'}
                          </span>
                          <span className="text-xs text-gray-400 dark:text-gray-500 truncate block">
                            {resource.id?.substring(0, 20)}...
                          </span>
                        </div>
                      </div>

                      {/* Status Badge */}
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold border ml-2 flex-shrink-0 ${health.status === 'healthy'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-800'
                          : health.status === 'stopped'
                            ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-800'
                            : 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800'
                        }`}>
                        {health.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>

      {/* Custom Scrollbar Styles */}
      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #D1D5DB;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #9CA3AF;
        }
        .dark .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #4B5563;
        }
        .dark .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #6B7280;
        }
        
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}
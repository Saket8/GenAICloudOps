import React, { useState, useEffect } from 'react';
import { ConversationAnalyticsResponse } from '../../types/chatbot';
import { chatbotService } from '../../services/chatbotService';

interface ChatAnalyticsProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ChatAnalytics({ isOpen, onClose }: ChatAnalyticsProps) {
  const [analytics, setAnalytics] = useState<ConversationAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<'1d' | '7d' | '30d' | '90d'>('7d');

  useEffect(() => {
    if (isOpen) {
      loadAnalytics();
    }
  }, [isOpen, selectedPeriod]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await chatbotService.getAnalytics(selectedPeriod);
      setAnalytics(data);
    } catch (err) {
      setError('Failed to load analytics');
      console.error('Error loading analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 1) return '<1s';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  const getPeriodLabel = (period: string) => {
    switch (period) {
      case '1d': return 'Last 24 hours';
      case '7d': return 'Last 7 days';
      case '30d': return 'Last 30 days';
      case '90d': return 'Last 90 days';
      default: return period;
    }
  };

  const renderMetricCard = (title: string, value: string | number, icon: string, description?: string) => (
    <div className="bg-white dark:bg-gray-700 p-4 rounded-lg border border-gray-200 dark:border-gray-600">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
            <i className={`${icon} text-blue-600 dark:text-blue-400 text-sm`}></i>
          </div>
        </div>
        <div className="ml-3 flex-1">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-white">{value}</p>
          {description && (
            <p className="text-xs text-gray-400 dark:text-gray-500">{description}</p>
          )}
        </div>
      </div>
    </div>
  );

  const renderIntentBreakdown = (intentBreakdown: Record<string, number>) => {
    const total = Object.values(intentBreakdown).reduce((sum, count) => sum + count, 0);
    if (total === 0) return null;

    return (
      <div className="bg-white dark:bg-gray-700 p-4 rounded-lg border border-gray-200 dark:border-gray-600">
        <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
          Intent Distribution
        </h4>
        <div className="space-y-2">
          {Object.entries(intentBreakdown)
            .sort(([,a], [,b]) => b - a)
            .map(([intent, count]) => {
              const percentage = ((count / total) * 100).toFixed(1);
              const intentIcon = chatbotService.getIntentIcon(intent);
              const intentColor = chatbotService.getIntentColor(intent);
              
              return (
                <div key={intent} className="flex items-center justify-between">
                  <div className="flex items-center flex-1">
                    <i className={`${intentIcon} text-gray-400 mr-2 text-sm`}></i>
                    <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">
                      {intent.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-500 dark:text-gray-400 w-12 text-right">
                      {count} ({percentage}%)
                    </span>
                  </div>
                </div>
              );
            })}
        </div>
      </div>
    );
  };

  const renderTopQueries = (topQueries: string[]) => {
    if (topQueries.length === 0) return null;

    return (
      <div className="bg-white dark:bg-gray-700 p-4 rounded-lg border border-gray-200 dark:border-gray-600">
        <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
          Popular Queries
        </h4>
        <div className="space-y-2">
          {topQueries.slice(0, 5).map((query, index) => (
            <div key={index} className="flex items-center">
              <span className="w-6 h-6 bg-gray-100 dark:bg-gray-600 rounded-full flex items-center justify-center text-xs font-medium text-gray-600 dark:text-gray-300 mr-3">
                {index + 1}
              </span>
              <span className="text-sm text-gray-700 dark:text-gray-300 truncate">
                {query}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderMostUsedTemplates = (templates: Array<{name: string; usage_count: number}>) => {
    if (templates.length === 0) return null;

    return (
      <div className="bg-white dark:bg-gray-700 p-4 rounded-lg border border-gray-200 dark:border-gray-600">
        <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
          Most Used Templates
        </h4>
        <div className="space-y-2">
          {templates.slice(0, 5).map((template, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex items-center">
                <span className="w-6 h-6 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center text-xs font-medium text-blue-600 dark:text-blue-400 mr-3">
                  {index + 1}
                </span>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {template.name}
                </span>
              </div>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {template.usage_count} uses
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div className="flex items-center space-x-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Chat Analytics
              </h3>
              
              {/* Period selector */}
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value as any)}
                className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="1d">Last 24 hours</option>
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
              </select>
            </div>
            
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <i className="fas fa-times"></i>
            </button>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
            {/* Error message */}
            {error && (
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                {error}
                <button
                  onClick={() => setError(null)}
                  className="float-right text-red-500 hover:text-red-700"
                >
                  <i className="fas fa-times"></i>
                </button>
              </div>
            )}

            {/* Loading state */}
            {loading && (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            )}

            {/* Analytics content */}
            {!loading && analytics && (
              <div className="space-y-6">
                {/* Overview metrics */}
                <div>
                  <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    Overview - {getPeriodLabel(analytics.period)}
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {renderMetricCard(
                      'Total Conversations',
                      formatNumber(analytics.total_conversations),
                      'fas fa-comments',
                      'Unique conversation sessions'
                    )}
                    {renderMetricCard(
                      'Total Messages',
                      formatNumber(analytics.total_messages),
                      'fas fa-message',
                      'Messages sent and received'
                    )}
                    {renderMetricCard(
                      'Tokens Used',
                      formatNumber(analytics.total_tokens),
                      'fas fa-microchip',
                      'AI processing tokens'
                    )}
                    {renderMetricCard(
                      'Avg Response Time',
                      formatDuration(analytics.avg_response_time),
                      'fas fa-clock',
                      'Average AI response time'
                    )}
                  </div>
                </div>

                {/* Detailed analytics */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Intent breakdown */}
                  {renderIntentBreakdown(analytics.intent_breakdown)}

                  {/* Top queries */}
                  {renderTopQueries(analytics.top_queries)}
                </div>

                {/* Most used templates */}
                <div className="grid grid-cols-1 lg:grid-cols-1 gap-6">
                  {renderMostUsedTemplates(analytics.most_used_templates)}
                </div>

                {/* Additional insights */}
                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <i className="fas fa-lightbulb text-blue-500 mt-1"></i>
                    </div>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200">
                        Insights
                      </h4>
                      <div className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                        <ul className="list-disc list-inside space-y-1">
                          {analytics.total_conversations > 0 && (
                            <li>
                              Average messages per conversation: {(analytics.total_messages / analytics.total_conversations).toFixed(1)}
                            </li>
                          )}
                          {analytics.total_tokens > 0 && analytics.total_messages > 0 && (
                            <li>
                              Average tokens per message: {(analytics.total_tokens / analytics.total_messages).toFixed(0)}
                            </li>
                          )}
                          {analytics.avg_response_time > 0 && (
                            <li>
                              Response time is{' '}
                              {analytics.avg_response_time < 2 ? 'excellent' : 
                               analytics.avg_response_time < 5 ? 'good' : 'could be improved'}
                            </li>
                          )}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
} 
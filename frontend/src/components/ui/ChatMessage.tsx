import React, { useState } from 'react';
import { ChatMessage as ChatMessageType, IntentResponse, TemplateResponse } from '../../types/chatbot';
import { chatbotService } from '../../services/chatbotService';

interface ChatMessageProps {
  message: ChatMessageType;
  onFeedback?: (rating: number, feedback?: string) => void;
  onTemplateSelect?: (template: TemplateResponse) => void;
  onRetry?: () => void;
}

export function ChatMessage({ message, onFeedback, onTemplateSelect, onRetry }: ChatMessageProps) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState(0);
  const [feedbackText, setFeedbackText] = useState('');
  const [showTemplates, setShowTemplates] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleFeedbackSubmit = () => {
    if (onFeedback && feedbackRating > 0) {
      onFeedback(feedbackRating, feedbackText);
      setShowFeedback(false);
      setFeedbackRating(0);
      setFeedbackText('');
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Loading state with animated dots
  const renderLoadingContent = () => (
    <div className="flex items-center space-x-3 py-2">
      <div className="flex space-x-1.5">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2.5 h-2.5 bg-gradient-to-r from-blue-400 to-indigo-500 rounded-full animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
      <span className="text-sm text-gray-500 dark:text-gray-400 italic animate-pulse">
        AI is thinking...
      </span>
    </div>
  );

  // Render message content
  const renderContent = () => {
    if (message.isLoading) {
      return renderLoadingContent();
    }

    return (
      <div
        className={`prose prose-sm max-w-none dark:prose-invert ${message.isUser
          ? 'prose-p:text-white prose-strong:text-white prose-code:text-blue-100'
          : 'prose-p:text-gray-700 dark:prose-p:text-gray-200'
          }`}
        dangerouslySetInnerHTML={{
          __html: chatbotService.parseMarkdown(message.content)
        }}
      />
    );
  };

  // Intent badge with gradient
  const renderIntent = (intent: IntentResponse) => {
    const iconClass = chatbotService.getIntentIcon(intent.intent_type);

    const intentColors: Record<string, string> = {
      'infrastructure_query': 'from-blue-500 to-cyan-500',
      'troubleshooting': 'from-orange-500 to-red-500',
      'monitoring_alert': 'from-purple-500 to-pink-500',
      'cost_optimization': 'from-green-500 to-emerald-500',
      'remediation_request': 'from-amber-500 to-orange-500',
      'resource_analysis': 'from-indigo-500 to-purple-500',
      'help_request': 'from-gray-500 to-slate-500',
      'general_chat': 'from-gray-400 to-gray-500',
    };

    const gradientClass = intentColors[intent.intent_type] || 'from-gray-500 to-gray-600';

    return (
      <div className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold text-white bg-gradient-to-r ${gradientClass} shadow-sm mb-3`}>
        <i className={`${iconClass} mr-1.5 text-white/90`} />
        <span className="capitalize">
          {intent.intent_type.replace(/_/g, ' ')}
        </span>
        <span className="ml-1.5 px-1.5 py-0.5 bg-white/20 rounded-full text-[10px]">
          {Math.round(intent.confidence_score * 100)}%
        </span>
      </div>
    );
  };

  // OCI Insights card
  const renderOCIInsights = (insights: Record<string, any>) => {
    if (!insights || Object.keys(insights).length === 0) return null;

    return (
      <div className="mt-4 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/30 dark:to-indigo-900/30 rounded-xl border border-blue-100 dark:border-blue-800/50 backdrop-blur-sm">
        <div className="flex items-center mb-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-sm mr-3">
            <i className="fas fa-cloud text-white text-sm" />
          </div>
          <span className="text-sm font-bold text-blue-900 dark:text-blue-100">
            OCI Insights
          </span>
        </div>

        <div className="space-y-2">
          {insights.compartment && (
            <div className="flex items-center text-sm text-gray-600 dark:text-gray-300">
              <i className="fas fa-folder text-blue-500 mr-2 w-4" />
              <span className="font-medium">Compartment:</span>
              <span className="ml-2">{insights.compartment.name || insights.compartment.id}</span>
            </div>
          )}

          {insights.alerts && insights.alerts.length > 0 && (
            <div className="text-sm text-gray-600 dark:text-gray-300">
              <div className="flex items-center">
                <i className="fas fa-bell text-amber-500 mr-2 w-4" />
                <span className="font-medium">Active Alerts:</span>
                <span className="ml-2 px-2 py-0.5 bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300 rounded-full text-xs font-bold">
                  {insights.alerts.length}
                </span>
              </div>
              <div className="ml-6 mt-2 space-y-1">
                {insights.alerts.slice(0, 2).map((alert: any, index: number) => (
                  <div key={index} className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mr-2" />
                    {alert.name || 'Alert'} ({alert.severity || 'Unknown'})
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Suggested templates
  const renderSuggestedTemplates = (templates: TemplateResponse[]) => {
    if (!templates || templates.length === 0) return null;

    return (
      <div className="mt-4">
        <button
          onClick={() => setShowTemplates(!showTemplates)}
          className="flex items-center text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
        >
          <i className={`fas fa-chevron-${showTemplates ? 'down' : 'right'} mr-2 text-xs transition-transform`} />
          <i className="fas fa-magic mr-2 text-purple-500" />
          Suggested Templates ({templates.length})
        </button>

        {showTemplates && (
          <div className="mt-3 space-y-2 animate-fadeIn">
            {templates.slice(0, 3).map((template) => (
              <button
                key={template.id}
                onClick={() => onTemplateSelect?.(template)}
                className="w-full text-left p-3 bg-gradient-to-r from-gray-50 to-white dark:from-gray-800 dark:to-gray-750 rounded-xl border border-gray-200 dark:border-gray-600 hover:border-purple-300 dark:hover:border-purple-500 hover:shadow-md transition-all duration-200 group"
              >
                <div className="flex items-center">
                  <div className="w-8 h-8 rounded-lg bg-purple-100 dark:bg-purple-900/50 flex items-center justify-center mr-3 group-hover:scale-110 transition-transform">
                    <i className="fas fa-file-alt text-purple-600 dark:text-purple-400 text-sm" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-gray-900 dark:text-white text-sm truncate">
                      {template.name}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                      {template.description}
                    </div>
                  </div>
                  <i className="fas fa-arrow-right text-gray-400 group-hover:text-purple-500 group-hover:translate-x-1 transition-all" />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  // Message action buttons
  const renderMessageActions = () => {
    if (message.isUser || message.isLoading) return null;

    return (
      <div className="flex items-center mt-3 pt-3 border-t border-gray-100 dark:border-gray-700/50">
        <div className="flex items-center space-x-1">
          {/* Feedback button */}
          <button
            onClick={() => setShowFeedback(!showFeedback)}
            className={`flex items-center px-2 py-1 rounded-lg text-xs font-medium transition-all ${showFeedback
              ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            title="Rate this response"
          >
            <i className="fas fa-thumbs-up mr-1.5" />
            Feedback
          </button>

          {/* Copy button */}
          <button
            onClick={handleCopy}
            className={`flex items-center px-2 py-1 rounded-lg text-xs font-medium transition-all ${copied
              ? 'bg-green-100 dark:bg-green-900/50 text-green-600 dark:text-green-400'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            title="Copy message"
          >
            <i className={`fas ${copied ? 'fa-check' : 'fa-copy'} mr-1.5`} />
            {copied ? 'Copied!' : 'Copy'}
          </button>

          {/* Retry button */}
          {onRetry && (
            <button
              onClick={onRetry}
              className="flex items-center px-2 py-1 rounded-lg text-xs font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-all"
              title="Regenerate response"
            >
              <i className="fas fa-redo mr-1.5" />
              Retry
            </button>
          )}
        </div>

        {/* Model info badge */}
        {message.model_used && (
          <div className="ml-auto flex items-center space-x-2 text-[10px] text-gray-400 dark:text-gray-500">
            <span className="flex items-center px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded-full">
              <i className="fas fa-microchip mr-1" />
              {message.model_used.split('/').pop()?.substring(0, 12) || message.model_used}
            </span>
            {message.tokens_used > 0 && (
              <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded-full">
                {message.tokens_used} tokens
              </span>
            )}
            {message.response_time && (
              <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded-full">
                {message.response_time.toFixed(2)}s
              </span>
            )}
            {message.cached && (
              <span className="px-2 py-0.5 bg-green-100 dark:bg-green-900/50 text-green-600 dark:text-green-400 rounded-full">
                <i className="fas fa-bolt mr-1" />
                cached
              </span>
            )}
          </div>
        )}
      </div>
    );
  };

  // Feedback form
  const renderFeedbackForm = () => {
    if (!showFeedback) return null;

    return (
      <div className="mt-4 p-4 bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-800 dark:to-gray-750 rounded-xl border border-gray-200 dark:border-gray-600 animate-fadeIn">
        <div className="mb-4">
          <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            How helpful was this response?
          </label>
          <div className="flex space-x-1">
            {[1, 2, 3, 4, 5].map((rating) => (
              <button
                key={rating}
                onClick={() => setFeedbackRating(rating)}
                className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${rating <= feedbackRating
                  ? 'bg-gradient-to-r from-yellow-400 to-amber-500 text-white shadow-lg scale-110'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-400 hover:bg-yellow-100 dark:hover:bg-yellow-900/30 hover:text-yellow-500'
                  }`}
              >
                <i className="fas fa-star text-sm" />
              </button>
            ))}
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Additional feedback (optional)
          </label>
          <textarea
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            className="w-full px-4 py-3 text-sm border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            rows={2}
            placeholder="Tell us how we can improve..."
          />
        </div>

        <div className="flex space-x-3">
          <button
            onClick={handleFeedbackSubmit}
            disabled={feedbackRating === 0}
            className="flex-1 px-4 py-2.5 text-sm font-semibold bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-lg transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
          >
            Submit Feedback
          </button>
          <button
            onClick={() => {
              setShowFeedback(false);
              setFeedbackRating(0);
              setFeedbackText('');
            }}
            className="px-4 py-2.5 text-sm font-medium border border-gray-300 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-all"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  };

  return (
    <div
      className={`flex ${message.isUser ? 'justify-end' : 'justify-start'} mb-4 animate-fadeIn`}
      style={{
        animationDelay: '0.1s',
        animationFillMode: 'both'
      }}
    >
      {/* AI Avatar */}
      {!message.isUser && (
        <div className="flex-shrink-0 mr-3">
          <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg">
            <i className="fas fa-robot text-white text-sm" />
            {/* Online indicator */}
            <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 rounded-full border-2 border-white dark:border-gray-900" />
          </div>
        </div>
      )}

      {/* Message Bubble */}
      <div
        className={`max-w-[85%] overflow-hidden ${message.isUser
          ? 'bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 text-white rounded-2xl rounded-tr-md shadow-lg shadow-blue-500/20'
          : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white rounded-2xl rounded-tl-md shadow-lg border border-gray-100 dark:border-gray-700'
          } px-5 py-4 transition-all duration-200 hover:shadow-xl`}
      >
        {/* Intent indicator */}
        {!message.isUser && message.intent && renderIntent(message.intent)}

        {/* Message content */}
        <div className="leading-relaxed break-words overflow-hidden">
          {renderContent()}
        </div>

        {/* OCI Insights */}
        {!message.isUser && message.oci_insights && renderOCIInsights(message.oci_insights)}

        {/* Suggested templates */}
        {!message.isUser && message.suggested_templates && renderSuggestedTemplates(message.suggested_templates)}

        {/* Timestamp */}
        <div className={`flex items-center mt-3 ${message.isUser ? 'text-white/70' : 'text-gray-400 dark:text-gray-500'
          }`}>
          <i className="fas fa-clock text-[10px] mr-1.5" />
          <span className="text-xs font-medium">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        {/* Message actions */}
        {renderMessageActions()}

        {/* Feedback form */}
        {renderFeedbackForm()}
      </div>

      {/* User Avatar */}
      {message.isUser && (
        <div className="flex-shrink-0 ml-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center shadow-lg">
            <i className="fas fa-user text-white text-sm" />
          </div>
        </div>
      )}

      {/* Custom Styles */}
      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
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
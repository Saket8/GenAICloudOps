import React, { useState, useEffect, useRef } from 'react';
import { ChatMessage } from '../ui/ChatMessage';
import { TypingIndicator } from '../ui/TypingIndicator';
import { TemplateSelector } from '../ui/TemplateSelector';
import { ConversationHistory } from '../ui/ConversationHistory';
import { ChatAnalytics } from '../ui/ChatAnalytics';
import {
  ChatMessage as ChatMessageType,
  EnhancedChatRequest,
  TemplateResponse,
  SuggestedQueriesResponse,
  ConversationResponse,
  ConversationWithMessagesResponse
} from '../../types/chatbot';
import { chatbotService } from '../../services/chatbotService';

interface ChatbotPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ChatbotPanel({ isOpen, onClose }: ChatbotPanelProps) {
  // State management
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [conversation, setConversation] = useState<ConversationResponse | null>(null);
  const [showTemplateSelector, setShowTemplateSelector] = useState(false);
  const [showConversationHistory, setShowConversationHistory] = useState(false);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [suggestedQueries, setSuggestedQueries] = useState<SuggestedQueriesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isMinimized, setIsMinimized] = useState(false);
  const [showSettingsSidebar, setShowSettingsSidebar] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Initialize chat
  useEffect(() => {
    if (isOpen && !sessionId) {
      initializeChat();
    }
  }, [isOpen]);

  // Auto-scroll to bottom
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen && !isMinimized) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 300);
    }
  }, [isOpen, isMinimized]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        onClose();
      }

      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        inputRef.current?.focus();
      }

      if ((e.ctrlKey || e.metaKey) && e.key === 'h') {
        e.preventDefault();
        setShowConversationHistory(true);
      }

      if ((e.ctrlKey || e.metaKey) && e.key === 't') {
        e.preventDefault();
        setShowTemplateSelector(true);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const initializeChat = async () => {
    try {
      const newSessionId = chatbotService.generateSessionId();
      setSessionId(newSessionId);

      const queries = await chatbotService.getSuggestedQueries();
      setSuggestedQueries(queries);

      const welcomeMessage: ChatMessageType = {
        id: 0,
        conversation_id: 0,
        role: 'assistant' as any,
        content: "Hello! I'm your **GenAI CloudOps Assistant** 🚀\n\nI can help you with:\n• Infrastructure queries & analysis\n• Cost optimization strategies\n• Troubleshooting & diagnostics\n• Performance monitoring insights\n\nHow can I assist you today?",
        model_used: 'system',
        tokens_used: 0,
        response_time: 0,
        cached: false,
        created_at: new Date().toISOString(),
        isUser: false,
        timestamp: new Date()
      };

      setMessages([welcomeMessage]);
      setError(null);
    } catch (err) {
      console.error('Failed to initialize chat:', err);
      setError('Failed to initialize chat. Please try again.');
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async (message?: string, templateVariables?: Record<string, any>) => {
    const messageText = message || inputMessage.trim();
    if (!messageText && !templateVariables) return;

    setIsLoading(true);
    setError(null);

    try {
      const userMessage: ChatMessageType = {
        id: messages.length + 1,
        conversation_id: conversation?.id || 0,
        role: 'user' as any,
        content: messageText,
        tokens_used: 0,
        cached: false,
        created_at: new Date().toISOString(),
        isUser: true,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, userMessage]);
      setInputMessage('');

      const chatRequest: EnhancedChatRequest = {
        message: messageText,
        session_id: sessionId,
        context: templateVariables || {},
        enable_intent_recognition: true,
        use_templates: true
      };

      const selectedCompartmentId =
        localStorage.getItem('selectedCompartmentId') ||
        localStorage.getItem('selectedCompartment');
      const selectedCloudProvider =
        localStorage.getItem('selectedCloudProvider') ||
        localStorage.getItem('selectedProvider');
      const ociContext: Record<string, any> = {};

      if (selectedCompartmentId) {
        ociContext.compartment_id = selectedCompartmentId;
      }
      if (selectedCloudProvider) {
        ociContext.cloud_provider = selectedCloudProvider;
      }

      if (Object.keys(ociContext).length > 0) {
        chatRequest.oci_context = ociContext;
      }

      const response = await chatbotService.sendMessage(chatRequest);

      if (!conversation && response.conversation_id) {
        try {
          const newConversation = await chatbotService.createConversation({
            title: chatbotService.formatConversationTitle(messageText)
          });
          setConversation(newConversation);
        } catch (convErr) {
          console.warn('Failed to create conversation record:', convErr);
        }
      }

      const aiMessage: ChatMessageType = {
        id: messages.length + 2,
        conversation_id: response.conversation_id || 0,
        role: 'assistant' as any,
        content: response.response,
        model_used: response.model,
        tokens_used: response.tokens_used,
        response_time: response.response_time,
        cached: response.cached,
        created_at: new Date().toISOString(),
        isUser: false,
        timestamp: new Date(),
        intent: response.intent,
        suggested_templates: response.suggested_templates,
        oci_insights: response.oci_insights
      };

      setMessages(prev => [...prev, aiMessage]);

    } catch (err) {
      console.error('Failed to send message:', err);
      setError('Failed to send message. Please try again.');

      const errorMessage: ChatMessageType = {
        id: messages.length + 2,
        conversation_id: 0,
        role: 'assistant' as any,
        content: "I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists.",
        tokens_used: 0,
        cached: false,
        created_at: new Date().toISOString(),
        isUser: false,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleTemplateSelect = (template: TemplateResponse, variables?: Record<string, any>) => {
    const formattedMessage = variables
      ? chatbotService.formatTemplateText(template.template_text, variables)
      : template.template_text;

    sendMessage(formattedMessage, variables);
    setShowTemplateSelector(false);
  };

  const handleConversationSelect = (conversationData: ConversationWithMessagesResponse) => {
    setConversation(conversationData.conversation);
    setSessionId(conversationData.conversation.session_id);

    const convertedMessages: ChatMessageType[] = conversationData.messages.map(msg => ({
      ...msg,
      isUser: msg.role === 'user',
      timestamp: new Date(msg.created_at)
    }));

    setMessages(convertedMessages);
    setShowConversationHistory(false);
  };

  const handleFeedback = async (messageId: number, rating: number, feedbackText?: string) => {
    try {
      await chatbotService.submitFeedback({
        session_id: sessionId,
        message_id: messageId,
        rating,
        feedback_text: feedbackText
      });
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    }
  };

  const handleRetry = () => {
    const lastUserMessage = [...messages].reverse().find(msg => msg.isUser);
    if (lastUserMessage) {
      sendMessage(lastUserMessage.content);
    }
  };

  const handleExportConversation = async (format: 'json' | 'csv' | 'markdown' = 'markdown') => {
    if (!sessionId) return;

    try {
      const exportData = await chatbotService.exportConversation(sessionId, {
        session_id: sessionId,
        format,
        include_metadata: true
      });

      chatbotService.downloadExport(exportData);
    } catch (err) {
      console.error('Failed to export conversation:', err);
      setError('Failed to export conversation');
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    initializeChat();
  };

  // Quick action queries
  const quickActions = suggestedQueries ? [
    { icon: 'fa-server', label: 'Resources', query: suggestedQueries.infrastructure_queries[0] },
    { icon: 'fa-chart-line', label: 'Metrics', query: suggestedQueries.monitoring_queries[0] },
    { icon: 'fa-dollar-sign', label: 'Costs', query: suggestedQueries.cost_queries[0] },
    { icon: 'fa-wrench', label: 'Troubleshoot', query: suggestedQueries.troubleshooting_queries[0] },
  ] : [];

  const latestAssistantModel = [...messages]
    .reverse()
    .find((msg) => !msg.isUser && msg.model_used && msg.model_used !== 'system')
    ?.model_used;
  const compactModelName = latestAssistantModel?.split('/').pop() || latestAssistantModel;
  const assistantHeaderSubtitle = isLoading
    ? 'Thinking...'
    : compactModelName
      ? `Infra-aware • ${compactModelName}`
      : 'Infra-aware CloudOps Helper';

  if (!isOpen) return null;

  return (
    <>
      {/* Glassmorphic Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm md:backdrop-blur-none md:bg-transparent transition-all duration-300"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Premium Chatbot Panel */}
      <div
        className={`fixed right-0 z-50 w-full sm:w-[480px] md:w-[33vw] md:min-w-[480px] md:max-w-[600px] max-w-full overflow-hidden transform transition-all duration-500 ease-out ${isOpen ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0 pointer-events-none'
          } ${isMinimized ? 'bottom-0 h-auto' : 'inset-y-0'}`}
        role="dialog"
        aria-label="AI Assistant Chat"
        aria-modal="true"
      >
        {/* Main Container with Glassmorphism */}
        <div
          className={`flex flex-col w-full overflow-hidden bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl shadow-2xl border-l border-white/20 dark:border-gray-700/50 transition-all duration-300 ${isMinimized ? 'rounded-tl-2xl' : 'h-full'
            }`}
          style={{
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 0 40px rgba(59, 130, 246, 0.1)'
          }}
        >
          {/* Premium Header */}
          <div className="relative overflow-hidden">
            {/* Gradient Background */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700" />

            {/* Animated Pattern Overlay */}
            <div
              className="absolute inset-0 opacity-20"
              style={{
                backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.3'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
              }}
            />

            {/* Header Content */}
            <div className="relative flex items-center justify-between p-4">
              <div className="flex items-center space-x-3">
                {/* Animated AI Avatar */}
                <div className="relative">
                  <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center shadow-lg ring-2 ring-white/30">
                    <i className="fas fa-robot text-white text-lg" />
                  </div>
                  {/* Pulse indicator */}
                  <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 rounded-full border-2 border-white animate-pulse" />
                </div>

                <div>
                  <h3 className="text-white font-bold text-base tracking-tight">
                    AI Assistant
                  </h3>
                  <p className="text-white/70 text-xs font-medium">
                    <span className="flex items-center">
                      <span className={isLoading ? 'animate-pulse' : ''}>{assistantHeaderSubtitle}</span>
                    </span>
                  </p>
                </div>
              </div>

              {/* Header Actions */}
              <div className="flex items-center space-x-1">
                {/* Settings Sidebar Toggle */}
                <button
                  onClick={() => setShowSettingsSidebar(!showSettingsSidebar)}
                  className="p-2 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white/30"
                  title="Settings"
                  aria-label="Open settings"
                >
                  <i className="fas fa-cog text-sm" />
                </button>

                {/* Analytics */}
                <button
                  onClick={() => setShowAnalytics(true)}
                  className="p-2 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white/30"
                  title="Analytics"
                  aria-label="View analytics"
                >
                  <i className="fas fa-chart-bar text-sm" />
                </button>

                {/* History */}
                <button
                  onClick={() => setShowConversationHistory(true)}
                  className="p-2 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white/30"
                  title="History (Ctrl+H)"
                  aria-label="View history"
                >
                  <i className="fas fa-history text-sm" />
                </button>

                {/* Export */}
                <button
                  onClick={() => handleExportConversation()}
                  className="p-2 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white/30"
                  title="Export"
                  aria-label="Export conversation"
                >
                  <i className="fas fa-download text-sm" />
                </button>

                {/* Templates */}
                <button
                  onClick={() => setShowTemplateSelector(true)}
                  className="p-2 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white/30"
                  title="Templates (Ctrl+T)"
                  aria-label="Open templates"
                >
                  <i className="fas fa-magic text-sm" />
                </button>

                {/* Minimize */}
                <button
                  onClick={() => setIsMinimized(!isMinimized)}
                  className="p-2 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white/30"
                  title={isMinimized ? "Expand" : "Minimize"}
                  aria-label={isMinimized ? "Expand chat" : "Minimize chat"}
                >
                  <i className={`fas ${isMinimized ? 'fa-window-restore' : 'fa-window-minimize'} text-sm`} />
                </button>

                {/* Close */}
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg text-white/80 hover:text-white hover:bg-red-500/50 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white/30"
                  title="Close (Esc)"
                  aria-label="Close chat"
                >
                  <i className="fas fa-times text-sm" />
                </button>
              </div>
            </div>
          </div>

          {!isMinimized && (
            <>
              {/* Settings Sidebar (Collapsible) */}
              {showSettingsSidebar && (
                <div className="absolute top-16 right-0 w-64 bg-white dark:bg-gray-800 shadow-xl rounded-l-2xl p-4 z-10 animate-slide-left border-l border-gray-100 dark:border-gray-700">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-semibold text-gray-900 dark:text-white">Quick Settings</h4>
                    <button
                      onClick={() => setShowSettingsSidebar(false)}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      <i className="fas fa-times text-sm" />
                    </button>
                  </div>

                  <div className="space-y-3">
                    <button
                      onClick={handleClearChat}
                      className="w-full flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
                    >
                      <i className="fas fa-trash-alt text-red-500 w-5" />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Clear Chat</span>
                    </button>
                    <button
                      onClick={() => handleExportConversation('json')}
                      className="w-full flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
                    >
                      <i className="fas fa-file-export text-blue-500 w-5" />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Export as JSON</span>
                    </button>
                    <button
                      onClick={() => handleExportConversation('markdown')}
                      className="w-full flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
                    >
                      <i className="fab fa-markdown text-purple-500 w-5" />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Export as Markdown</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Error Banner */}
              {error && (
                <div className="mx-4 mt-4 p-3 bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-200 dark:border-red-800 rounded-xl backdrop-blur-sm animate-shake" role="alert">
                  <div className="flex items-center">
                    <i className="fas fa-exclamation-circle text-red-500 mr-2" />
                    <span className="text-sm text-red-700 dark:text-red-300 flex-1">{error}</span>
                    <button
                      onClick={() => setError(null)}
                      className="text-red-500 hover:text-red-700 focus:outline-none"
                      aria-label="Dismiss error"
                    >
                      <i className="fas fa-times" />
                    </button>
                  </div>
                </div>
              )}

              {/* Messages Container */}
              <div
                ref={messagesContainerRef}
                className="flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-4 scroll-smooth min-w-0"
                style={{
                  backgroundImage: 'radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.03) 0%, transparent 50%)'
                }}
                role="log"
                aria-label="Conversation messages"
                aria-live="polite"
              >
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                    onFeedback={(rating, feedback) => handleFeedback(message.id, rating, feedback)}
                    onTemplateSelect={handleTemplateSelect}
                    onRetry={message.isUser ? undefined : handleRetry}
                  />
                ))}

                <TypingIndicator show={isLoading} />
                <div ref={messagesEndRef} aria-hidden="true" />
              </div>

              {/* Quick Actions Bar */}
              {quickActions.length > 0 && messages.length <= 1 && (
                <div className="px-4 pb-2">
                  <div className="flex flex-wrap gap-2" role="group" aria-label="Quick actions">
                    {quickActions.map((action, index) => (
                      <button
                        key={index}
                        onClick={() => action.query && sendMessage(action.query)}
                        className="group flex items-center space-x-2 px-3 py-2 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-xl border border-gray-200 dark:border-gray-600 hover:border-blue-300 dark:hover:border-blue-500 hover:shadow-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        title={action.query}
                      >
                        <i className={`fas ${action.icon} text-blue-500 group-hover:scale-110 transition-transform`} />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-200">{action.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Premium Input Area */}
              <div className="p-4 border-t border-gray-100 dark:border-gray-800 bg-gradient-to-t from-gray-50/50 to-transparent dark:from-gray-900/50">
                <div className="relative">
                  {/* Input Container with Glow Effect */}
                  <div
                    className="relative rounded-2xl bg-white dark:bg-gray-800 shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden transition-all duration-200 focus-within:border-blue-400 focus-within:ring-4 focus-within:ring-blue-500/10"
                    style={{
                      boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05), inset 0 2px 4px rgba(255, 255, 255, 0.1)'
                    }}
                  >
                    <label htmlFor="chat-input" className="sr-only">Type your message</label>
                    <textarea
                      id="chat-input"
                      ref={inputRef}
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Ask about resources, metrics, or get help..."
                      className="w-full px-4 py-3 pr-14 bg-transparent text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 text-sm resize-none focus:outline-none"
                      rows={2}
                      disabled={isLoading}
                      aria-describedby="chat-input-help"
                    />

                    {/* Send Button */}
                    <button
                      onClick={() => sendMessage()}
                      disabled={!inputMessage.trim() || isLoading}
                      className={`absolute right-2 bottom-2 w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-blue-500 ${inputMessage.trim() && !isLoading
                        ? 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg hover:shadow-xl hover:scale-105 active:scale-95'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                        }`}
                      aria-label={isLoading ? "Sending..." : "Send message"}
                    >
                      <i className={`fas ${isLoading ? 'fa-spinner fa-spin' : 'fa-paper-plane'} text-sm`} />
                    </button>
                  </div>

                  {/* Input Hints */}
                  <div className="flex items-center justify-between mt-2 px-1">
                    <p className="text-xs text-gray-400 dark:text-gray-500">
                      <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Enter</kbd> to send · <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Shift+Enter</kbd> for new line
                    </p>
                    <span className="text-xs text-gray-400 dark:text-gray-500">
                      {inputMessage.length}/2000
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Modals */}
      <TemplateSelector
        isOpen={showTemplateSelector}
        onClose={() => setShowTemplateSelector(false)}
        onTemplateSelect={handleTemplateSelect}
      />

      <ConversationHistory
        isOpen={showConversationHistory}
        onClose={() => setShowConversationHistory(false)}
        onConversationSelect={handleConversationSelect}
      />

      <ChatAnalytics
        isOpen={showAnalytics}
        onClose={() => setShowAnalytics(false)}
      />

      {/* Custom Animation Styles */}
      <style>{`
        @keyframes slide-left {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
          20%, 40%, 60%, 80% { transform: translateX(2px); }
        }
        
        .animate-slide-left {
          animation: slide-left 0.3s ease-out;
        }
        
        .animate-shake {
          animation: shake 0.5s ease-in-out;
        }
      `}</style>
    </>
  );
}

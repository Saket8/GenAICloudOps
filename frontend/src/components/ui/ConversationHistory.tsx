import React, { useState, useEffect } from 'react';
import {
  ConversationResponse,
  ConversationListResponse,
  ConversationStatus,
  ConversationWithMessagesResponse
} from '../../types/chatbot';
import { chatbotService } from '../../services/chatbotService';

interface ConversationHistoryProps {
  isOpen: boolean;
  onClose: () => void;
  onConversationSelect: (conversation: ConversationWithMessagesResponse) => void;
}

export function ConversationHistory({ isOpen, onClose, onConversationSelect }: ConversationHistoryProps) {
  const [conversations, setConversations] = useState<ConversationResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<ConversationStatus | ''>('');
  const [selectedConversation, setSelectedConversation] = useState<ConversationResponse | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalConversations, setTotalConversations] = useState(0);
  const perPage = 10;

  useEffect(() => {
    if (isOpen) {
      loadConversations();
    }
  }, [isOpen, currentPage, statusFilter]);

  const loadConversations = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        page: currentPage,
        per_page: perPage
      };

      if (statusFilter) {
        params.status_filter = statusFilter;
      }

      const response = await chatbotService.getConversations(params);
      setConversations(response.conversations);
      setTotalConversations(response.total);
      setTotalPages(Math.ceil(response.total / perPage));
    } catch (err) {
      setError('Failed to load conversations');
      console.error('Error loading conversations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleConversationClick = async (conversation: ConversationResponse) => {
    try {
      setSelectedConversation(conversation);
      const fullConversation = await chatbotService.getConversationWithMessages(conversation.session_id);
      onConversationSelect(fullConversation);
      onClose();
    } catch (err) {
      setError('Failed to load conversation details');
      console.error('Error loading conversation details:', err);
    }
  };

  const handleArchiveConversation = async (conversation: ConversationResponse) => {
    try {
      await chatbotService.archiveConversation(conversation.session_id);
      loadConversations(); // Reload the list
    } catch (err) {
      setError('Failed to archive conversation');
      console.error('Error archiving conversation:', err);
    }
  };

  const handleExportConversation = async (conversation: ConversationResponse, format: 'json' | 'csv' | 'markdown' = 'markdown') => {
    try {
      const exportData = await chatbotService.exportConversation(conversation.session_id, {
        session_id: conversation.session_id,
        format,
        include_metadata: true
      });
      chatbotService.downloadExport(exportData);
    } catch (err) {
      setError('Failed to export conversation');
      console.error('Error exporting conversation:', err);
    }
  };

  const filteredConversations = conversations.filter(conv => {
    if (!searchQuery) return true;
    const searchLower = searchQuery.toLowerCase();
    return conv.title?.toLowerCase().includes(searchLower) ||
           conv.session_id.toLowerCase().includes(searchLower);
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays - 1} days ago`;
    
    return date.toLocaleDateString();
  };

  const getStatusColor = (status: ConversationStatus) => {
    switch (status) {
      case ConversationStatus.ACTIVE:
        return 'bg-green-100 text-green-800';
      case ConversationStatus.ARCHIVED:
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const renderConversationItem = (conversation: ConversationResponse) => (
    <div
      key={conversation.id}
      className="p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer"
      onClick={() => handleConversationClick(conversation)}
    >
      <div className="flex justify-between items-start">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {conversation.title || `Conversation ${conversation.id}`}
            </h4>
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(conversation.status)}`}>
              {conversation.status}
            </span>
          </div>
          
          <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
            <span>{formatDate(conversation.created_at)}</span>
            <span>{conversation.total_messages} messages</span>
            <span>{conversation.total_tokens_used} tokens</span>
          </div>
          
          {conversation.last_activity && (
            <div className="text-xs text-gray-400 mt-1">
              Last activity: {formatDate(conversation.last_activity)}
            </div>
          )}
        </div>

        <div className="flex items-center space-x-1 ml-2">
          {/* Export dropdown */}
          <div className="relative group">
            <button
              onClick={(e) => {
                e.stopPropagation();
              }}
              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              title="Export conversation"
            >
              <i className="fas fa-download text-sm"></i>
            </button>
            <div className="absolute right-0 top-full mt-1 w-32 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleExportConversation(conversation, 'markdown');
                }}
                className="block w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                Markdown
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleExportConversation(conversation, 'json');
                }}
                className="block w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                JSON
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleExportConversation(conversation, 'csv');
                }}
                className="block w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                CSV
              </button>
            </div>
          </div>

          {/* Archive button */}
          {conversation.status === ConversationStatus.ACTIVE && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleArchiveConversation(conversation);
              }}
              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              title="Archive conversation"
            >
              <i className="fas fa-archive text-sm"></i>
            </button>
          )}
        </div>
      </div>
    </div>
  );

  const renderFilters = () => (
    <div className="space-y-3 mb-4">
      {/* Search */}
      <div className="relative">
        <i className="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search conversations..."
          className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Status filter */}
      <select
        value={statusFilter}
        onChange={(e) => setStatusFilter(e.target.value as ConversationStatus | '')}
        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">All Conversations</option>
        <option value={ConversationStatus.ACTIVE}>Active</option>
        <option value={ConversationStatus.ARCHIVED}>Archived</option>
      </select>
    </div>
  );

  const renderPagination = () => {
    if (totalPages <= 1) return null;

    return (
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Page {currentPage} of {totalPages} ({totalConversations} total)
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
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
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Conversation History
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <i className="fas fa-times"></i>
            </button>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
            {/* Filters */}
            {renderFilters()}

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

            {/* Conversations list */}
            {!loading && (
              <>
                {filteredConversations.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    {conversations.length === 0 ? 'No conversations found' : 'No conversations match your search'}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredConversations.map(renderConversationItem)}
                  </div>
                )}

                {/* Pagination */}
                {renderPagination()}
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
} 
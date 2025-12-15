import { api } from './apiClient';
import {
  EnhancedChatRequest,
  EnhancedChatResponse,
  ConversationCreateRequest,
  ConversationResponse,
  ConversationListResponse,
  ConversationWithMessagesResponse,
  UseTemplateRequest,
  TemplateListResponse,
  ConversationExportRequest,
  ConversationExportResponse,
  ConversationAnalyticsResponse,
  ChatbotFeedbackRequest,
  FeedbackResponse,
  ChatbotHealthResponse,
  SuggestedQueriesResponse,
  ConversationStatus
} from '../types/chatbot';

class ChatbotService {
  private readonly baseUrl = '/chatbot';

  // Enhanced Chat Methods
  async sendMessage(request: EnhancedChatRequest): Promise<EnhancedChatResponse> {
    const response = await api.post<EnhancedChatResponse>(`${this.baseUrl}/chat/enhanced`, request);
    return response.data;
  }

  async getSuggestedQueries(): Promise<SuggestedQueriesResponse> {
    const response = await api.get<SuggestedQueriesResponse>(`${this.baseUrl}/suggestions`);
    return response.data;
  }

  // Conversation Management
  async createConversation(request?: ConversationCreateRequest): Promise<ConversationResponse> {
    const response = await api.post<ConversationResponse>(`${this.baseUrl}/conversations`, request || {});
    return response.data;
  }

  async getConversations(params?: {
    page?: number;
    per_page?: number;
    status_filter?: ConversationStatus;
  }): Promise<ConversationListResponse> {
    const response = await api.get<ConversationListResponse>(`${this.baseUrl}/conversations`, { params });
    return response.data;
  }

  async getConversationWithMessages(sessionId: string): Promise<ConversationWithMessagesResponse> {
    const response = await api.get<ConversationWithMessagesResponse>(`${this.baseUrl}/conversations/${sessionId}`);
    return response.data;
  }

  async archiveConversation(sessionId: string): Promise<{message: string}> {
    const response = await api.patch<{message: string}>(`${this.baseUrl}/conversations/${sessionId}/archive`);
    return response.data;
  }

  // Query Templates
  async getTemplates(params?: {
    category?: string;
    search?: string;
  }): Promise<TemplateListResponse> {
    const response = await api.get<TemplateListResponse>(`${this.baseUrl}/templates`, { params });
    return response.data;
  }

  async useTemplate(templateId: number, request?: UseTemplateRequest): Promise<EnhancedChatResponse> {
    const response = await api.post<EnhancedChatResponse>(
      `${this.baseUrl}/templates/${templateId}/use`, 
      { template_id: templateId, ...request }
    );
    return response.data;
  }

  // Export and Analytics
  async exportConversation(sessionId: string, request?: ConversationExportRequest): Promise<ConversationExportResponse> {
    const exportRequest = { session_id: sessionId, ...request };
    const response = await api.post<ConversationExportResponse>(
      `${this.baseUrl}/conversations/${sessionId}/export`, 
      exportRequest
    );
    return response.data;
  }

  async getAnalytics(period: '1d' | '7d' | '30d' | '90d' = '7d'): Promise<ConversationAnalyticsResponse> {
    const response = await api.get<ConversationAnalyticsResponse>(`${this.baseUrl}/analytics`, {
      params: { period }
    });
    return response.data;
  }

  // Feedback
  async submitFeedback(request: ChatbotFeedbackRequest): Promise<FeedbackResponse> {
    const response = await api.post<FeedbackResponse>(`${this.baseUrl}/feedback`, request);
    return response.data;
  }

  // Health and Status
  async getHealth(): Promise<ChatbotHealthResponse> {
    const response = await api.get<ChatbotHealthResponse>(`${this.baseUrl}/health`);
    return response.data;
  }

  // Utility methods for frontend
  generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  formatConversationTitle(firstMessage: string): string {
    const maxLength = 50;
    const title = firstMessage.trim();
    return title.length > maxLength ? `${title.substring(0, maxLength)}...` : title;
  }

  categorizeTemplates(templates: TemplateListResponse) {
    const categories: Record<string, any[]> = {};
    
    templates.templates.forEach(template => {
      if (!categories[template.category]) {
        categories[template.category] = [];
      }
      categories[template.category].push(template);
    });

    return Object.keys(categories).map(category => ({
      name: category,
      templates: categories[category],
      count: categories[category].length
    }));
  }

  extractVariablesFromTemplate(templateText: string): string[] {
    const variableRegex = /\{([^}]+)\}/g;
    const variables: string[] = [];
    let match;
    
    while ((match = variableRegex.exec(templateText)) !== null) {
      if (!variables.includes(match[1])) {
        variables.push(match[1]);
      }
    }
    
    return variables;
  }

  validateTemplateVariables(templateText: string, variables: Record<string, any>): {
    isValid: boolean;
    missingVariables: string[];
  } {
    const requiredVariables = this.extractVariablesFromTemplate(templateText);
    const missingVariables = requiredVariables.filter(
      variable => !variables.hasOwnProperty(variable) || !variables[variable]
    );
    
    return {
      isValid: missingVariables.length === 0,
      missingVariables
    };
  }

  formatTemplateText(templateText: string, variables: Record<string, any>): string {
    let formatted = templateText;
    
    Object.keys(variables).forEach(variable => {
      const regex = new RegExp(`\\{${variable}\\}`, 'g');
      formatted = formatted.replace(regex, variables[variable]);
    });
    
    return formatted;
  }

  // Message utilities
  parseMarkdown(text: string): string {
    // Basic markdown parsing for chat messages
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      .replace(/\n/g, '<br>');
  }

  // Export utilities
  downloadExport(exportData: ConversationExportResponse): void {
    const blob = new Blob([exportData.content], { 
      type: this.getContentType(exportData.format) 
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = exportData.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  private getContentType(format: string): string {
    switch (format) {
      case 'json':
        return 'application/json';
      case 'csv':
        return 'text/csv';
      case 'markdown':
        return 'text/markdown';
      default:
        return 'text/plain';
    }
  }

  // Search and filtering utilities
  searchConversations(conversations: ConversationWithMessagesResponse[], query: string) {
    const lowercaseQuery = query.toLowerCase();
    return conversations.filter(conv => {
      // Search in conversation title
      if (conv.conversation.title?.toLowerCase().includes(lowercaseQuery)) {
        return true;
      }
      
      // Search in message content
      return conv.messages.some(message => 
        message.content.toLowerCase().includes(lowercaseQuery)
      );
    });
  }

  filterConversationsByDateRange(
    conversations: ConversationWithMessagesResponse[], 
    startDate: Date, 
    endDate: Date
  ) {
    return conversations.filter(conv => {
      const convDate = new Date(conv.conversation.created_at);
      return convDate >= startDate && convDate <= endDate;
    });
  }

  // Intent and analytics utilities
  getIntentIcon(intentType: string): string {
    const icons: Record<string, string> = {
      'general_chat': 'fas fa-comments',
      'infrastructure_query': 'fas fa-server',
      'troubleshooting': 'fas fa-tools',
      'resource_analysis': 'fas fa-chart-line',
      'cost_optimization': 'fas fa-dollar-sign',
      'monitoring_alert': 'fas fa-exclamation-triangle',
      'remediation_request': 'fas fa-magic',
      'help_request': 'fas fa-question-circle'
    };
    return icons[intentType] || 'fas fa-comment';
  }

  getIntentColor(intentType: string): string {
    const colors: Record<string, string> = {
      'general_chat': 'bg-blue-100 text-blue-800',
      'infrastructure_query': 'bg-green-100 text-green-800',
      'troubleshooting': 'bg-red-100 text-red-800',
      'resource_analysis': 'bg-purple-100 text-purple-800',
      'cost_optimization': 'bg-yellow-100 text-yellow-800',
      'monitoring_alert': 'bg-orange-100 text-orange-800',
      'remediation_request': 'bg-indigo-100 text-indigo-800',
      'help_request': 'bg-gray-100 text-gray-800'
    };
    return colors[intentType] || 'bg-gray-100 text-gray-800';
  }
}

export const chatbotService = new ChatbotService(); 
// Enums
export enum ConversationStatus {
  ACTIVE = "active",
  ARCHIVED = "archived",
  DELETED = "deleted"
}

export enum MessageRole {
  USER = "user",
  ASSISTANT = "assistant",
  SYSTEM = "system"
}

export enum IntentType {
  GENERAL_CHAT = "general_chat",
  INFRASTRUCTURE_QUERY = "infrastructure_query",
  TROUBLESHOOTING = "troubleshooting",
  RESOURCE_ANALYSIS = "resource_analysis",
  COST_OPTIMIZATION = "cost_optimization",
  MONITORING_ALERT = "monitoring_alert",
  REMEDIATION_REQUEST = "remediation_request",
  HELP_REQUEST = "help_request"
}

// Request Types
export interface EnhancedChatRequest {
  message: string;
  session_id?: string;
  context?: Record<string, any>;
  oci_context?: Record<string, any>;
  enable_intent_recognition?: boolean;
  use_templates?: boolean;
}

export interface ConversationCreateRequest {
  title?: string;
  context?: Record<string, any>;
}

export interface UseTemplateRequest {
  template_id: number;
  variables?: Record<string, any>;
  session_id?: string;
  context?: Record<string, any>;
}

export interface ConversationExportRequest {
  session_id: string;
  format?: 'json' | 'csv' | 'markdown';
  include_metadata?: boolean;
}

export interface ChatbotFeedbackRequest {
  session_id: string;
  message_id?: number;
  rating: number; // 1-5 scale
  feedback_text?: string;
  feedback_type?: string;
}

// Response Types
export interface IntentResponse {
  intent_type: IntentType;
  confidence_score: number;
  entities?: Record<string, any>;
}

export interface TemplateResponse {
  id: number;
  name: string;
  description?: string;
  category: string;
  template_text: string;
  variables?: Record<string, any>;
  usage_count: number;
  requires_role?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface EnhancedChatResponse {
  response: string;
  session_id: string;
  conversation_id?: number;
  model: string;
  tokens_used: number;
  response_time: number;
  cached: boolean;
  intent?: IntentResponse;
  suggested_templates: TemplateResponse[];
  oci_insights?: Record<string, any>;
}

export interface MessageResponse {
  id: number;
  conversation_id: number;
  role: MessageRole;
  content: string;
  model_used?: string;
  tokens_used: number;
  response_time?: number;
  cached: boolean;
  context_snapshot?: Record<string, any>;
  created_at: string;
}

export interface ConversationResponse {
  id: number;
  session_id: string;
  user_id: number;
  title?: string;
  status: ConversationStatus;
  context?: Record<string, any>;
  total_messages: number;
  total_tokens_used: number;
  last_activity?: string;
  created_at: string;
  updated_at?: string;
}

export interface ConversationListResponse {
  conversations: ConversationResponse[];
  total: number;
  page: number;
  per_page: number;
}

export interface ConversationWithMessagesResponse {
  conversation: ConversationResponse;
  messages: MessageResponse[];
}

export interface TemplateListResponse {
  templates: TemplateResponse[];
  total: number;
  categories: string[];
}

export interface ConversationExportResponse {
  session_id: string;
  format: string;
  content: string;
  filename: string;
  exported_at: string;
}

export interface ConversationAnalyticsResponse {
  user_id: number;
  period: string;
  total_conversations: number;
  total_messages: number;
  total_tokens: number;
  avg_response_time: number;
  intent_breakdown: Record<string, number>;
  top_queries: string[];
  most_used_templates: Array<{name: string; usage_count: number}>;
}

export interface FeedbackResponse {
  id: number;
  conversation_id: number;
  message_id: number;
  user_id: number;
  rating: number;
  feedback_text?: string;
  feedback_type?: string;
  created_at: string;
}

export interface ChatbotHealthResponse {
  status: string;
  database_connection: boolean;
  redis_connection: boolean;
  ai_service: boolean;
  intent_recognition: boolean;
  total_conversations: number;
  active_sessions: number;
  avg_response_time: number;
}

export interface SuggestedQueriesResponse {
  infrastructure_queries: string[];
  monitoring_queries: string[];
  troubleshooting_queries: string[];
  cost_queries: string[];
}

// UI-specific types
export interface ChatMessage extends MessageResponse {
  isUser: boolean;
  timestamp: Date;
  isLoading?: boolean;
  intent?: IntentResponse;
  suggested_templates?: TemplateResponse[];
  oci_insights?: Record<string, any>;
}

export interface ConversationSummary {
  id: number;
  session_id: string;
  title?: string;
  last_message?: string;
  last_activity: Date;
  message_count: number;
  status: ConversationStatus;
}

export interface TemplateCategory {
  name: string;
  templates: TemplateResponse[];
  count: number;
}

export interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onTemplateSelect?: (template: TemplateResponse) => void;
  placeholder?: string;
  disabled?: boolean;
  isLoading?: boolean;
  suggestedQueries?: string[];
}

export interface QuickAction {
  id: string;
  label: string;
  query: string;
  icon?: string;
  category?: string;
}

// Error types
export interface ChatbotError {
  message: string;
  code?: string;
  details?: any;
} 
import apiClient from './apiClient';

export interface ChatRequest {
  message: string;
  session_id?: string;
  context?: Record<string, any>;
}

export interface ChatResponse {
  content: string;
  session_id: string;
  context: Record<string, any>;
  model: string;
  tokens_used: number;
  response_time: number;
}

export interface RemediationRequest {
  issue_details: string;
  environment: string;
  service_name: string;
  severity: string;
  resource_info: Record<string, any>;
}

export interface AnalysisRequest {
  data: Record<string, any>;
  context?: string;
}

export interface GenAIResponse {
  content: string;
  model: string;
  tokens_used: number;
  response_time: number;
  request_id: string;
  timestamp: string;
}

class GenAIService {
  async chatCompletion(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post('/genai/chat', request);
    return response.data;
  }

  async getRemediationSuggestions(request: RemediationRequest): Promise<GenAIResponse> {
    const response = await apiClient.post('/genai/remediation', request);
    return response.data;
  }

  async analyzeData(request: AnalysisRequest): Promise<GenAIResponse> {
    const response = await apiClient.post('/genai/analyze', request);
    return response.data;
  }

  async explainAlert(alertData: any): Promise<GenAIResponse> {
    const request: AnalysisRequest = {
      data: alertData,
      context: "Explain this alert in simple terms and provide context about why it occurred."
    };
    return this.analyzeData(request);
  }

  async getOptimizationSuggestions(resourceData: any): Promise<GenAIResponse> {
    const request: AnalysisRequest = {
      data: resourceData,
      context: "Analyze this resource usage and provide optimization recommendations."
    };
    return this.analyzeData(request);
  }

  async troubleshootIssue(issueData: any): Promise<GenAIResponse> {
    const request: AnalysisRequest = {
      data: issueData,
      context: "Provide troubleshooting steps and potential solutions for this issue."
    };
    return this.analyzeData(request);
  }
}

export const genaiService = new GenAIService(); 
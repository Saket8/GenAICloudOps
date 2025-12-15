import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { tokenManager } from './authService';

// API Base URL - can be configured via environment variable
const API_BASE_URL = (import.meta as any)?.env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Create axios instance with default configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120 seconds timeout for heavy OCI operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add authentication token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    const token = tokenManager.getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized - attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Attempt to refresh the token
        const refreshToken = tokenManager.getRefreshToken();
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        // Call refresh endpoint
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        // Store new tokens
        tokenManager.setTokens({
          access_token: response.data.access_token,
          refresh_token: response.data.refresh_token || refreshToken,
          token_type: response.data.token_type || 'bearer',
          expires_in: response.data.expires_in || 3600,
        });

        // Retry the original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
        }

        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed - clear tokens and redirect to login
        console.error('Token refresh failed:', refreshError);
        tokenManager.clearTokens();

        // Dispatch event for auth context to handle
        window.dispatchEvent(new CustomEvent('auth:token-expired'));

        return Promise.reject(error);
      }
    }

    // Handle other error responses
    return Promise.reject(error);
  }
);

// Add the required types
interface RequestConfig {
  params?: any;
  headers?: any;
  baseURL?: string; // Add this line
  timeout?: number; // Add this line
  // Add other axios config options as needed
}

// Utility functions for common HTTP methods
export const api = {
  // GET request
  get: <T = any>(url: string, config?: RequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.get<T>(url, config);
  },

  // POST request
  post: <T = any, D = any>(
    url: string,
    data?: D,
    config?: RequestConfig
  ): Promise<AxiosResponse<T>> => {
    return apiClient.post<T>(url, data, config);
  },

  // PUT request
  put: <T = any, D = any>(
    url: string,
    data?: D,
    config?: RequestConfig
  ): Promise<AxiosResponse<T>> => {
    return apiClient.put<T>(url, data, config);
  },

  // PATCH request
  patch: <T = any, D = any>(
    url: string,
    data?: D,
    config?: RequestConfig
  ): Promise<AxiosResponse<T>> => {
    return apiClient.patch<T>(url, data, config);
  },

  // DELETE request
  delete: <T = any>(url: string, config?: RequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.delete<T>(url, config);
  },
};

// Export the configured axios instance for direct use if needed
export default apiClient;
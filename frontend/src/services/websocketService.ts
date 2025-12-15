/**
 * WebSocket Service for Real-time Data Updates
 * Handles WebSocket connections, subscriptions, and real-time data streaming
 */

export enum MessageType {
  // Connection management
  CONNECT = 'connect',
  DISCONNECT = 'disconnect',
  PING = 'ping',
  PONG = 'pong',
  
  // Subscriptions
  SUBSCRIBE = 'subscribe',
  UNSUBSCRIBE = 'unsubscribe',
  
  // Data streams
  METRICS_UPDATE = 'metrics_update',
  ALERT_NOTIFICATION = 'alert_notification',
  ACTION_STATUS_UPDATE = 'action_status_update',
  RESOURCE_UPDATE = 'resource_update',
  COST_UPDATE = 'cost_update',
  
  // System messages
  ERROR = 'error',
  SUCCESS = 'success',
  HEARTBEAT = 'heartbeat'
}

export enum SubscriptionType {
  DASHBOARD_METRICS = 'dashboard_metrics',
  ALERTS = 'alerts',
  REMEDIATION_ACTIONS = 'remediation_actions',
  KUBERNETES_PODS = 'kubernetes_pods',
  COST_ANALYSIS = 'cost_analysis',
  SYSTEM_HEALTH = 'system_health'
}

export interface WebSocketMessage {
  type: MessageType;
  data: any;
  timestamp: string;
  subscription?: SubscriptionType;
  user_id?: string;
}

export interface SystemMetrics {
  timestamp: string;
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  network_io: {
    bytes_sent: number;
    bytes_recv: number;
    packets_sent: number;
    packets_recv: number;
  };
  active_connections: number;
  uptime_seconds: number;
}

export interface AlertData {
  id: string;
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'critical';
  source: string;
  timestamp: string;
  resolved?: boolean;
}

export interface ActionUpdate {
  action_id: string;
  action_type: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number;
  message: string;
  timestamp: string;
  estimated_completion?: string;
}

export interface CostUpdate {
  type: string;
  data: {
    current_month_cost: number;
    cost_change_percent: number;
    top_costly_resource: {
      name: string;
      cost: number;
      type: string;
    };
    optimization_savings: number;
    timestamp: string;
  };
}

type MessageHandler = (message: WebSocketMessage) => void;
type MetricsHandler = (metrics: SystemMetrics) => void;
type AlertHandler = (alert: AlertData) => void;
type ActionHandler = (action: ActionUpdate) => void;
type CostHandler = (cost: CostUpdate) => void;
type ErrorHandler = (error: string) => void;
type ConnectionHandler = (connected: boolean) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private token: string | null = null;
  private baseUrl: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private isConnecting = false;
  private isManualDisconnect = false;
  
  // Subscriptions
  private subscriptions = new Set<SubscriptionType>();
  
  // Event handlers
  private messageHandlers = new Map<MessageType, Set<MessageHandler>>();
  private metricsHandlers = new Set<MetricsHandler>();
  private alertHandlers = new Set<AlertHandler>();
  private actionHandlers = new Set<ActionHandler>();
  private costHandlers = new Set<CostHandler>();
  private errorHandlers = new Set<ErrorHandler>();
  private connectionHandlers = new Set<ConnectionHandler>();
  
  constructor() {
    // Determine WebSocket URL based on current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.NODE_ENV === 'development' 
      ? 'localhost:8000' 
      : window.location.host;
    this.baseUrl = `${protocol}//${host}/api/v1/ws/connect`;
    
    // Setup periodic connection health check
    setInterval(() => this.healthCheck(), 30000); // Every 30 seconds
    
    // Setup token refresh check (every 5 minutes)
    setInterval(() => this.checkTokenExpiration(), 300000); // Every 5 minutes
  }
  
  /**
   * Connect to WebSocket server
   */
  async connect(token: string): Promise<boolean> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return true;
    }
    
    this.token = token;
    this.isConnecting = true;
    this.isManualDisconnect = false;
    
    try {
      const wsUrl = `${this.baseUrl}?token=${encodeURIComponent(token)}`;
      console.log('🔌 Connecting to WebSocket:', wsUrl.replace(token, '[TOKEN]'));
      
      this.ws = new WebSocket(wsUrl);
      
      return new Promise((resolve, reject) => {
        if (!this.ws) {
          reject(new Error('Failed to create WebSocket'));
          return;
        }
        
        const timeout = setTimeout(() => {
          reject(new Error('Connection timeout'));
        }, 10000);
        
        this.ws.onopen = () => {
          clearTimeout(timeout);
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;
          console.log('✅ WebSocket connected');
          
          // Start heartbeat
          this.startHeartbeat();
          
          // Notify connection handlers
          this.connectionHandlers.forEach(handler => handler(true));
          
          // Re-subscribe to previous subscriptions
          this.resubscribeAll();
          
          resolve(true);
        };
        
        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };
        
        this.ws.onclose = (event) => {
          clearTimeout(timeout);
          this.isConnecting = false;
          console.log('🔌 WebSocket disconnected:', event.code, event.reason);
          
          // Stop heartbeat
          this.stopHeartbeat();
          
          // Notify connection handlers
          this.connectionHandlers.forEach(handler => handler(false));
          
          // Attempt reconnection if not manual disconnect
          if (!this.isManualDisconnect && this.token) {
            this.scheduleReconnect();
          }
          
          if (event.code !== 1000) { // Not normal closure
            reject(new Error(`Connection failed: ${event.reason || event.code}`));
          }
        };
        
        this.ws.onerror = (error) => {
          clearTimeout(timeout);
          console.error('❌ WebSocket error:', error);
          this.errorHandlers.forEach(handler => handler('WebSocket connection error'));
          reject(error);
        };
      });
      
    } catch (error) {
      this.isConnecting = false;
      console.error('❌ Failed to connect to WebSocket:', error);
      throw error;
    }
  }
  
  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.isManualDisconnect = true;
    this.stopHeartbeat();
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    
    this.subscriptions.clear();
    console.log('🔌 WebSocket disconnected manually');
  }
  
  /**
   * Subscribe to a data stream
   */
  async subscribe(subscriptionType: SubscriptionType): Promise<boolean> {
    if (!this.isConnected()) {
      console.warn('⚠️ Cannot subscribe: WebSocket not connected');
      return false;
    }
    
    if (this.subscriptions.has(subscriptionType)) {
      console.log(`✅ Already subscribed to ${subscriptionType}`);
      return true;
    }
    
    const message: WebSocketMessage = {
      type: MessageType.SUBSCRIBE,
      data: { subscription: subscriptionType },
      timestamp: new Date().toISOString()
    };
    
    this.sendMessage(message);
    this.subscriptions.add(subscriptionType);
    console.log(`📡 Subscribed to ${subscriptionType}`);
    return true;
  }
  
  /**
   * Unsubscribe from a data stream
   */
  async unsubscribe(subscriptionType: SubscriptionType): Promise<boolean> {
    if (!this.isConnected()) {
      return false;
    }
    
    const message: WebSocketMessage = {
      type: MessageType.UNSUBSCRIBE,
      data: { subscription: subscriptionType },
      timestamp: new Date().toISOString()
    };
    
    this.sendMessage(message);
    this.subscriptions.delete(subscriptionType);
    console.log(`📡 Unsubscribed from ${subscriptionType}`);
    return true;
  }
  
  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
  
  /**
   * Get current subscriptions
   */
  getSubscriptions(): SubscriptionType[] {
    return Array.from(this.subscriptions);
  }
  
  /**
   * Add message handler
   */
  onMessage(type: MessageType, handler: MessageHandler): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set());
    }
    this.messageHandlers.get(type)!.add(handler);
  }
  
  /**
   * Remove message handler
   */
  offMessage(type: MessageType, handler: MessageHandler): void {
    this.messageHandlers.get(type)?.delete(handler);
  }
  
  /**
   * Add metrics handler
   */
  onMetrics(handler: MetricsHandler): void {
    this.metricsHandlers.add(handler);
  }
  
  /**
   * Remove metrics handler
   */
  offMetrics(handler: MetricsHandler): void {
    this.metricsHandlers.delete(handler);
  }
  
  /**
   * Add alert handler
   */
  onAlert(handler: AlertHandler): void {
    this.alertHandlers.add(handler);
  }
  
  /**
   * Remove alert handler
   */
  offAlert(handler: AlertHandler): void {
    this.alertHandlers.delete(handler);
  }
  
  /**
   * Add action handler
   */
  onAction(handler: ActionHandler): void {
    this.actionHandlers.add(handler);
  }
  
  /**
   * Remove action handler
   */
  offAction(handler: ActionHandler): void {
    this.actionHandlers.delete(handler);
  }
  
  /**
   * Add cost handler
   */
  onCost(handler: CostHandler): void {
    this.costHandlers.add(handler);
  }
  
  /**
   * Remove cost handler
   */
  offCost(handler: CostHandler): void {
    this.costHandlers.delete(handler);
  }
  
  /**
   * Add error handler
   */
  onError(handler: ErrorHandler): void {
    this.errorHandlers.add(handler);
  }
  
  /**
   * Remove error handler
   */
  offError(handler: ErrorHandler): void {
    this.errorHandlers.delete(handler);
  }
  
  /**
   * Add connection status handler
   */
  onConnection(handler: ConnectionHandler): void {
    this.connectionHandlers.add(handler);
  }
  
  /**
   * Remove connection status handler
   */
  offConnection(handler: ConnectionHandler): void {
    this.connectionHandlers.delete(handler);
  }
  
  /**
   * Send message to server
   */
  private sendMessage(message: WebSocketMessage): void {
    if (this.isConnected() && this.ws) {
      this.ws.send(JSON.stringify(message));
    }
  }
  
  /**
   * Handle incoming message
   */
  private handleMessage(data: string): void {
    try {
      const message: WebSocketMessage = JSON.parse(data);
      
      // Handle specific message types
      switch (message.type) {
        case MessageType.METRICS_UPDATE:
          if (message.data?.type === 'system_metrics') {
            this.metricsHandlers.forEach(handler => handler(message.data.data));
          }
          break;
          
        case MessageType.ALERT_NOTIFICATION:
          if (message.data?.type === 'new_alert' || message.data?.type === 'custom_alert') {
            this.alertHandlers.forEach(handler => handler(message.data.data));
          }
          break;
          
        case MessageType.ACTION_STATUS_UPDATE:
          this.actionHandlers.forEach(handler => handler(message.data));
          break;
          
        case MessageType.COST_UPDATE:
          this.costHandlers.forEach(handler => handler(message.data));
          break;
          
        case MessageType.ERROR:
          const errorMsg = message.data?.error || 'Unknown WebSocket error';
          console.error('❌ WebSocket error:', errorMsg);
          this.errorHandlers.forEach(handler => handler(errorMsg));
          break;
          
        case MessageType.PONG:
          // Heartbeat response received
          break;
          
        default:
          // Handle generic message handlers
          const handlers = this.messageHandlers.get(message.type);
          if (handlers) {
            handlers.forEach(handler => handler(message));
          }
          break;
      }
      
    } catch (error) {
      console.error('❌ Failed to parse WebSocket message:', error, data);
    }
  }
  
  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        const ping: WebSocketMessage = {
          type: MessageType.PING,
          data: { timestamp: new Date().toISOString() },
          timestamp: new Date().toISOString()
        };
        this.sendMessage(ping);
      }
    }, 30000); // Ping every 30 seconds
  }
  
  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
  
  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnection attempts reached');
      this.errorHandlers.forEach(handler => 
        handler('Connection lost. Please refresh the page to reconnect.')
      );
      return;
    }
    
    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`🔄 Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    setTimeout(async () => {
      if (!this.isManualDisconnect && this.token) {
        try {
          await this.connect(this.token);
        } catch (error) {
          console.error('❌ Reconnection failed:', error);
        }
      }
    }, delay);
  }
  
  /**
   * Re-subscribe to all previous subscriptions
   */
  private async resubscribeAll(): Promise<void> {
    const currentSubscriptions = Array.from(this.subscriptions);
    this.subscriptions.clear();
    
    for (const subscription of currentSubscriptions) {
      await this.subscribe(subscription);
    }
  }
  
  /**
   * Health check for connection
   */
  private healthCheck(): void {
    if (!this.isConnected() && !this.isConnecting && !this.isManualDisconnect && this.token) {
      console.log('🔄 Health check: reconnecting...');
      this.connect(this.token).catch(error => {
        console.error('❌ Health check reconnection failed:', error);
      });
    }
  }

  /**
   * Check if token is expiring soon and refresh connection
   */
  private async checkTokenExpiration(): Promise<void> {
    if (!this.token || !this.isConnected()) {
      return;
    }

    try {
      // Decode JWT token to check expiration
      const tokenParts = this.token.split('.');
      if (tokenParts.length !== 3) {
        return;
      }

      const payload = JSON.parse(atob(tokenParts[1]));
      const exp = payload.exp * 1000; // Convert to milliseconds
      const now = Date.now();
      const timeUntilExpiry = exp - now;

      // If token expires in less than 5 minutes, try to refresh
      if (timeUntilExpiry < 5 * 60 * 1000) { // 5 minutes
        console.log('🔄 Token expiring soon, attempting to refresh connection...');
        
        // Get fresh token from auth service
        const { tokenManager } = await import('../services/authService');
        const newToken = tokenManager.getToken();
        
        if (newToken && newToken !== this.token) {
          console.log('🔄 Got fresh token, reconnecting...');
          // Disconnect and reconnect with new token
          this.disconnect();
          await this.connect(newToken);
        }
      }
    } catch (error) {
      console.error('❌ Token expiration check failed:', error);
    }
  }
}

// Global WebSocket service instance
export const websocketService = new WebSocketService(); 
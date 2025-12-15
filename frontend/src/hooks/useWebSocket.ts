/**
 * React Hooks for WebSocket Integration
 * Provides easy-to-use hooks for real-time data in React components
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { websocketService, SubscriptionType, SystemMetrics, AlertData, ActionUpdate, CostUpdate } from '../services/websocketService';
import { tokenManager } from '../services/authService';

export interface UseWebSocketOptions {
  autoConnect?: boolean;
  subscriptions?: SubscriptionType[];
}

export interface WebSocketState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  subscriptions: SubscriptionType[];
}

/**
 * Main WebSocket hook for connection management
 */
export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const { autoConnect = true, subscriptions = [] } = options;
  
  const [state, setState] = useState<WebSocketState>({
    connected: false,
    connecting: false,
    error: null,
    subscriptions: []
  });
  
  const connectingRef = useRef(false);
  
  // Get token from auth service
  const getToken = useCallback(() => {
    return tokenManager.getToken();
  }, []);
  
  const connect = useCallback(async () => {
    if (connectingRef.current) return;
    
    const token = getToken();
    if (!token) {
      setState(prev => ({ ...prev, error: 'No authentication token available' }));
      return;
    }
    
    try {
      connectingRef.current = true;
      setState(prev => ({ ...prev, connecting: true, error: null }));
      
      await websocketService.connect(token);
      
      // Subscribe to requested subscriptions
      for (const subscription of subscriptions) {
        await websocketService.subscribe(subscription);
      }
      
      setState(prev => ({
        ...prev,
        connected: true,
        connecting: false,
        subscriptions: websocketService.getSubscriptions()
      }));
      
    } catch (error) {
      setState(prev => ({
        ...prev,
        connected: false,
        connecting: false,
        error: error instanceof Error ? error.message : 'Connection failed'
      }));
    } finally {
      connectingRef.current = false;
    }
  }, [getToken, subscriptions]);
  
  const disconnect = useCallback(() => {
    websocketService.disconnect();
    setState(prev => ({
      ...prev,
      connected: false,
      connecting: false,
      subscriptions: []
    }));
  }, []);
  
  const subscribe = useCallback(async (subscriptionType: SubscriptionType) => {
    await websocketService.subscribe(subscriptionType);
    setState(prev => ({
      ...prev,
      subscriptions: websocketService.getSubscriptions()
    }));
  }, []);
  
  const unsubscribe = useCallback(async (subscriptionType: SubscriptionType) => {
    await websocketService.unsubscribe(subscriptionType);
    setState(prev => ({
      ...prev,
      subscriptions: websocketService.getSubscriptions()
    }));
  }, []);
  
  useEffect(() => {
    // Connection status handler
    const handleConnection = (connected: boolean) => {
      setState(prev => ({ ...prev, connected }));
    };
    
    // Error handler with automatic reconnection for auth errors
    const handleError = (error: string) => {
      setState(prev => ({ ...prev, error }));
      
      // If it's an authentication error, try to reconnect with fresh token
      if (error.includes('Authentication') || error.includes('token') || error.includes('Forbidden')) {
        console.log('🔄 Authentication error detected, attempting reconnection...');
        setTimeout(() => {
          connect().catch(console.error);
        }, 2000); // Wait 2 seconds before retry
      }
    };
    
    websocketService.onConnection(handleConnection);
    websocketService.onError(handleError);
    
    // Auto-connect if enabled
    if (autoConnect) {
      connect();
    }
    
    return () => {
      websocketService.offConnection(handleConnection);
      websocketService.offError(handleError);
    };
  }, [autoConnect, connect]);
  
  return {
    ...state,
    connect,
    disconnect,
    subscribe,
    unsubscribe
  };
};

/**
 * Hook for real-time system metrics
 */
export const useSystemMetrics = () => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  
  useEffect(() => {
    const handleMetrics = (newMetrics: SystemMetrics) => {
      setMetrics(newMetrics);
      setLastUpdated(new Date());
    };
    
    websocketService.onMetrics(handleMetrics);
    
    return () => {
      websocketService.offMetrics(handleMetrics);
    };
  }, []);
  
  return { metrics, lastUpdated };
};

/**
 * Hook for real-time alerts
 */
export const useAlerts = () => {
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  
  const markAsRead = useCallback((alertId: string) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, read: true } : alert
    ));
    setUnreadCount(prev => Math.max(0, prev - 1));
  }, []);
  
  const markAllAsRead = useCallback(() => {
    setAlerts(prev => prev.map(alert => ({ ...alert, read: true })));
    setUnreadCount(0);
  }, []);
  
  const removeAlert = useCallback((alertId: string) => {
    setAlerts(prev => {
      const filtered = prev.filter(alert => alert.id !== alertId);
      const removedAlert = prev.find(alert => alert.id === alertId);
      if (removedAlert && !(removedAlert as any).read) {
        setUnreadCount(count => Math.max(0, count - 1));
      }
      return filtered;
    });
  }, []);
  
  useEffect(() => {
    const handleAlert = (newAlert: AlertData) => {
      setAlerts(prev => [{ ...newAlert, read: false } as any, ...prev].slice(0, 50)); // Keep last 50 alerts
      setUnreadCount(prev => prev + 1);
    };
    
    websocketService.onAlert(handleAlert);
    
    return () => {
      websocketService.offAlert(handleAlert);
    };
  }, []);
  
  return {
    alerts,
    unreadCount,
    markAsRead,
    markAllAsRead,
    removeAlert
  };
};

/**
 * Hook for real-time action updates
 */
export const useActionUpdates = () => {
  const [actions, setActions] = useState<Map<string, ActionUpdate>>(new Map());
  
  const getAction = useCallback((actionId: string) => {
    return actions.get(actionId);
  }, [actions]);
  
  const getAllActions = useCallback(() => {
    return Array.from(actions.values()).sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }, [actions]);
  
  const getActiveActions = useCallback(() => {
    return Array.from(actions.values()).filter(action => 
      action.status === 'pending' || action.status === 'in_progress'
    );
  }, [actions]);
  
  useEffect(() => {
    const handleAction = (actionUpdate: ActionUpdate) => {
      setActions(prev => new Map(prev.set(actionUpdate.action_id, actionUpdate)));
    };
    
    websocketService.onAction(handleAction);
    
    return () => {
      websocketService.offAction(handleAction);
    };
  }, []);
  
  return {
    getAction,
    getAllActions,
    getActiveActions,
    activeCount: getActiveActions().length
  };
};

/**
 * Hook for real-time cost updates
 */
export const useCostUpdates = () => {
  const [costData, setCostData] = useState<CostUpdate | null>(null);
  const [history, setHistory] = useState<CostUpdate[]>([]);
  
  useEffect(() => {
    const handleCost = (costUpdate: CostUpdate) => {
      setCostData(costUpdate);
      setHistory(prev => [costUpdate, ...prev].slice(0, 10)); // Keep last 10 updates
    };
    
    websocketService.onCost(handleCost);
    
    return () => {
      websocketService.offCost(handleCost);
    };
  }, []);
  
  return { costData, history };
};

/**
 * Hook for WebSocket connection status
 */
export const useConnectionStatus = () => {
  const [connected, setConnected] = useState(false);
  const [lastConnected, setLastConnected] = useState<Date | null>(null);
  const [lastDisconnected, setLastDisconnected] = useState<Date | null>(null);
  
  useEffect(() => {
    const handleConnection = (isConnected: boolean) => {
      setConnected(isConnected);
      if (isConnected) {
        setLastConnected(new Date());
      } else {
        setLastDisconnected(new Date());
      }
    };
    
    websocketService.onConnection(handleConnection);
    
    // Check initial state
    setConnected(websocketService.isConnected());
    
    return () => {
      websocketService.offConnection(handleConnection);
    };
  }, []);
  
  return {
    connected,
    lastConnected,
    lastDisconnected
  };
}; 
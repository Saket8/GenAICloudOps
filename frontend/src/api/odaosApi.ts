/**
 * ODAOS API Client — All calls to /api/v1/odaos/* with JWT auth.
 */
import axios from 'axios';

const API_BASE = '/api/v1/odaos';

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('genai_access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const odaosAxios = axios.create({ baseURL: 'http://localhost:8000' });
odaosAxios.interceptors.request.use((config) => {
  const headers = getAuthHeader();
  Object.assign(config.headers, headers);
  return config;
});

// --- Chat ---

export async function sendChatMessage(message: string, sessionId?: string, includeViz = true) {
  const { data } = await odaosAxios.post(`${API_BASE}/chat`, {
    message,
    session_id: sessionId,
    include_viz: includeViz,
  });
  return data;
}

export function streamChat(
  message: string,
  sessionId: string | null,
  onToken: (text: string) => void,
  onChart: (chart: any) => void,
  onSuggestions: (items: string[]) => void,
  onUsage: (data: any) => void,
  onDone: (sid: string) => void,
  onError: (msg: string) => void,
): () => void {
  const token = localStorage.getItem('genai_access_token');
  const params = new URLSearchParams({
    message,
    include_viz: 'true',
  });
  if (sessionId) params.set('session_id', sessionId);

  // EventSource doesn't support headers, so we use fetch + ReadableStream
  const abortController = new AbortController();

  (async () => {
    try {
      const resp = await fetch(
        `http://localhost:8000${API_BASE}/chat/stream?${params}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          signal: abortController.signal,
        },
      );

      if (!resp.ok) {
        onError(`HTTP ${resp.status}`);
        return;
      }

      const reader = resp.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let eventType = 'token';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            try {
              const payload = JSON.parse(line.slice(6));
              switch (eventType) {
                case 'token':
                  onToken(payload.content || '');
                  break;
                case 'chart':
                  onChart(payload.data || payload);
                  break;
                case 'suggestions':
                  onSuggestions(payload.items || []);
                  break;
                case 'usage':
                  onUsage(payload.data || payload);
                  break;
                case 'done':
                  if (payload.usage) onUsage(payload.usage);
                  onDone(payload.session_id || '');
                  break;
                case 'error':
                  onError(payload.message || 'Unknown error');
                  break;
              }
            } catch (err: any) {
              console.error("SSE parse/dispatch error: ", err);
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        onError(err.message || 'Connection error');
      }
    }
  })();

  return () => abortController.abort();
}

// --- Viz ---

export async function smartViz(query: string, chartType = 'auto', filters?: Record<string, any>) {
  const { data } = await odaosAxios.post(`${API_BASE}/viz/smart`, {
    query,
    chart_type: chartType,
    filters,
  });
  return data;
}

// --- Prompts ---

export async function listPrompts(params: {
  category?: string;
  search?: string;
  tag?: string;
  difficulty?: string;
  page?: number;
  per_page?: number;
}) {
  const { data } = await odaosAxios.get(`${API_BASE}/prompts`, { params });
  return data;
}

export async function listCategories() {
  const { data } = await odaosAxios.get(`${API_BASE}/prompts/categories`);
  return data;
}

export async function getPrompt(promptId: string) {
  const { data } = await odaosAxios.get(`${API_BASE}/prompts/${promptId}`);
  return data;
}

export async function getFavorites() {
  const { data } = await odaosAxios.get(`${API_BASE}/prompts/favorites`);
  return data;
}

export async function toggleFavorite(promptId: string) {
  const { data } = await odaosAxios.post(`${API_BASE}/prompts/${promptId}/favorite`);
  return data;
}

export async function getPromptHistory(limit = 20, offset = 0) {
  const { data } = await odaosAxios.get(`${API_BASE}/prompts/history`, {
    params: { limit, offset },
  });
  return data;
}

export function streamPromptExecution(
  promptId: string,
  parameters: Record<string, any>,
  customQuery: string | undefined,
  onToken: (text: string) => void,
  onChart: (chart: any) => void,
  onUsage: (data: any) => void,
  onDone: (meta: any) => void,
  onError: (msg: string) => void,
): () => void {
  const token = localStorage.getItem('genai_access_token');
  const abortController = new AbortController();

  (async () => {
    try {
      const resp = await fetch(
        `http://localhost:8000${API_BASE}/prompts/${promptId}/execute`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ parameters, custom_query: customQuery }),
          signal: abortController.signal,
        },
      );

      if (!resp.ok) {
        onError(`HTTP ${resp.status}`);
        return;
      }

      const reader = resp.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let eventType = 'token';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
            console.log("ODAOS_EVENT:", eventType);
          } else if (line.startsWith('data: ')) {
            try {
              const payload = JSON.parse(line.slice(6));
              if (eventType === 'usage' || eventType === 'done') {
                console.log(`ODAOS_DATA FOR ${eventType}:`, payload);
              }
              switch (eventType) {
                case 'token':
                  onToken(payload.content || '');
                  break;
                case 'chart':
                  onChart(payload.data || payload);
                  break;
                case 'usage':
                  console.log("dispatching usage");
                  onUsage(payload.data || payload);
                  break;
                case 'done':
                  if (payload.usage) onUsage(payload.usage);
                  console.log("dispatching done");
                  onDone(payload);
                  break;
                case 'error':
                  onError(payload.message || 'Execution error');
                  break;
              }
            } catch (err: any) {
              console.error("SSE parse/dispatch error in Prompts: ", err);
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        onError(err.message || 'Connection error');
      }
    }
  })();

  return () => abortController.abort();
}

// --- Sessions ---

export async function listSessions() {
  const { data } = await odaosAxios.get(`${API_BASE}/sessions`);
  return data;
}

// --- Health ---

export async function getOdaosHealth() {
  const { data } = await odaosAxios.get(`${API_BASE}/health`);
  return data;
}

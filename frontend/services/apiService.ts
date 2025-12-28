// frontend/services/apiService.ts - FIXED

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json();
        return { error: error.detail || 'Request failed' };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      return { error: 'Network error occurred' };
    }
  }

  // Auth endpoints
  async register(userData: any) {
    const response = await this.request<{ user: any; access_token: string; token_type: string }>(
      '/api/auth/register',
      {
        method: 'POST',
        body: JSON.stringify(userData),
      }
    );

    if (response.data) {
      // CHANGED: Use 'access_token' instead of 'auth_token'
      localStorage.setItem('access_token', response.data.access_token);
      // Keep auth_token for backward compatibility
      localStorage.setItem('auth_token', response.data.access_token);
    }

    return response;
  }

  async login(email: string, password: string) {
    const response = await this.request<{ access_token: string; token_type: string }>(
      '/api/auth/login',
      {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }
    );

    if (response.data) {
      // CHANGED: Use 'access_token' instead of 'auth_token'
      localStorage.setItem('access_token', response.data.access_token);
      // Keep auth_token for backward compatibility
      localStorage.setItem('auth_token', response.data.access_token);
    }

    return response;
  }

  async getCurrentUser() {
    // CHANGED: Try 'access_token' first, fallback to 'auth_token'
    const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
    if (!token) {
      return { error: 'No token found' };
    }

    return this.request('/api/auth/me', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('auth_token');
  }

  // Health check
  async healthCheck() {
    return this.request('/health', { method: 'GET' });
  }

  // NEW: Method to get token for WebSocket
  getToken(): string | null {
    return localStorage.getItem('access_token') || localStorage.getItem('auth_token');
  }
}

export const apiService = new ApiService();

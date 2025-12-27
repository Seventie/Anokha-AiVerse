// frontend/services/apiService.ts

const API_BASE_URL = 'http://localhost:8000';

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
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
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
      // Store token
      localStorage.setItem('auth_token', response.data.access_token);
    }

    return response;
  }

  async getCurrentUser() {
    const token = localStorage.getItem('auth_token');
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
    localStorage.removeItem('auth_token');
  }

  // Health check
  async healthCheck() {
    return this.request('/health', { method: 'GET' });
  }
}

export const apiService = new ApiService();
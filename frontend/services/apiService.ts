// frontend/services/apiService.ts - IMPROVED

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
      const url = `${this.baseUrl}${endpoint}`;
      console.log(`🔵 ${options.method || 'GET'} ${url}`);
      
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      // Log response status
      console.log(`📊 Response status: ${response.status}`);

      if (!response.ok) {
        let errorMessage = 'Request failed';
        
        try {
          const errorData = await response.json();
          console.error('❌ Error response:', errorData);
          
          // Handle 422 validation errors
          if (response.status === 422 && errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              errorMessage = errorData.detail
                .map((err: any) => `${err.loc.join('.')}: ${err.msg}`)
                .join(', ');
            } else {
              errorMessage = errorData.detail;
            }
          } else {
            errorMessage = errorData.detail || errorData.message || errorMessage;
          }
        } catch (e) {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        
        return { error: errorMessage };
      }

      const data = await response.json();
      console.log('✅ Success response:', data);
      return { data };
    } catch (error: any) {
      console.error('❌ Network error:', error);
      return { error: error.message || 'Network error occurred' };
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
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('auth_token', response.data.access_token); // Backward compatibility
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
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('auth_token', response.data.access_token); // Backward compatibility
    }

    return response;
  }

  async getCurrentUser() {
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

  // Get token for WebSocket
  getToken(): string | null {
    return localStorage.getItem('access_token') || localStorage.getItem('auth_token');
  }
}

export const apiService = new ApiService();

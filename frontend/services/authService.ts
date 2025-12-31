// frontend/src/services/authService.ts - FIXED

import { apiService } from './apiService';

export interface User {
  id: string;
  email: string;
  username: string;
  fullName: string;
  location?: string;
  preferredLocations?: string[];
  currentStatus?: string;
  fieldOfInterest?: string;
  targetRole?: string;
  timeline?: string;
  visionStatement?: string;
  readiness_level?: string;
  is_demo?: boolean;
  created_at?: string;
  education?: any[];
  skills?: any[];
  projects?: any[];
  experience?: any[];
  availability?: any;
}

interface AuthResponse {
  user?: User;
  error?: string;
}

class AuthService {
  // ✅ FIXED: Handle "Not authenticated" errors properly
  async getSession(): Promise<{ user: User | null; token: string | null }> {
    try {
      const token = apiService.getToken();
      
      if (!token) {
        console.log('⚠️ No token found in localStorage');
        return { user: null, token: null };
      }

      console.log('🔍 Validating token with backend...');
      
      // Try to get current user
      const response = await this.getCurrentUser();
      
      // ✅ FIX: If error (like "Not authenticated"), clear token
      if (response.error) {
        console.warn('⚠️ Token invalid or expired:', response.error);
        this.logout(); // Clear the bad token
        return { user: null, token: null };
      }
      
      if (response.user) {
        console.log('✅ Token valid, user loaded:', response.user.email);
        return { user: response.user, token };
      }

      // No user and no error = something weird, clear token
      console.warn('⚠️ Unexpected state, clearing token');
      this.logout();
      return { user: null, token: null };
      
    } catch (error: any) {
      console.error('❌ getSession error:', error);
      // ✅ Clear token on any error
      this.logout();
      return { user: null, token: null };
    }
  }

  async login(email: string, password: string): Promise<AuthResponse> {
    try {
      console.log('🔐 AuthService: Logging in with', email);
      
      const response = await apiService.login(email, password);
      
      if (response.error) {
        console.error('❌ AuthService: Login failed:', response.error);
        return { error: response.error };
      }
      
      if (response.data?.access_token) {
        console.log('✅ AuthService: Token received, fetching user profile...');
        
        // Fetch user profile
        const userResponse = await apiService.getCurrentUser();
        
        if (userResponse.error) {
          console.error('❌ AuthService: Failed to fetch user:', userResponse.error);
          return { error: userResponse.error };
        }
        
        if (userResponse.data) {
          console.log('✅ AuthService: User profile loaded:', userResponse.data);
          return { user: userResponse.data as User };
        }
      }
      
      return { error: 'Login failed. Please try again.' };
    } catch (error: any) {
      console.error('❌ AuthService: Login exception:', error);
      return { error: error.message || 'Login failed. Please try again.' };
    }
  }

  async getCurrentUser(): Promise<AuthResponse> {
    try {
      const response = await apiService.getCurrentUser();
      
      if (response.error) {
        return { error: response.error };
      }
      
      if (response.data) {
        return { user: response.data as User };
      }
      
      return { error: 'Failed to fetch user profile' };
    } catch (error: any) {
      return { error: error.message || 'Failed to fetch user profile' };
    }
  }

  logout(): void {
    console.log('🚪 Logging out, clearing tokens...');
    apiService.logout();
    localStorage.removeItem('user'); // ✅ Also clear stored user
  }

  isAuthenticated(): boolean {
    return !!apiService.getToken();
  }

  // ✅ Helper method to get token
  getToken(): string | null {
    return apiService.getToken();
  }

  // ✅ Helper method to get stored user
  getStoredUser(): User | null {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch {
        return null;
      }
    }
    return null;
  }
}

export const authService = new AuthService();
